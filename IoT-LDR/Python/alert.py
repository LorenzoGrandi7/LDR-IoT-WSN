"""
Copyright 2024 Lorenzo Grandi

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import asyncio
import logging
import json
from time import sleep
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import telegram
from io import BytesIO

from comm import DBClient, LdrSensorManager
from sensorInfo import *

WHITE = "\033[0m"
BLACK = "\033[30m"
RED = "\033[31m"
LIME = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
LIGHT_GRAY = "\033[37m"
BOLD = "\033[1m"
ITALIC = "\033[3m"

logger = logging.getLogger('alert unit')
logger.setLevel(logging.INFO)

last_pred_hour = -1
last_pred_min = -1

async def load_default_config() -> dict:
    """
    Load the default configuration settings from a JSON file.

    Returns
    -------
    dict
        Dictionary containing the default configuration settings.
    """
    logger.debug("Loading default configurations")
    with open('default_config.json', 'r') as f:
        return json.load(f)

async def load_sensors_config() -> dict:
    """
    Load sensor-specific configuration settings from a JSON file.

    Returns
    -------
    dict
        Dictionary containing the sensor configuration settings.
    """
    logger.debug("Loading sensors configurations")
    with open('sensors_config.json', 'r') as f:
        return json.load(f)

async def setup_sensors(default_config: dict, sensors_config: dict) -> list[LdrSensorManager]:
    """
    Create and configure sensor managers based on the provided configurations.

    Parameters
    ----------
    default_config : dict
        Dictionary containing default configuration settings.
    sensors_config : dict
        Dictionary containing sensor-specific configurations.

    Returns
    -------
    list
        List of initialized `LdrSensorManager` objects for the sensors.
    """
    logger.debug("Setting up LDR sensors")
    
    # Extract common configurations
    mqtt_cfg = default_config['mqtt']
    influxdb_cfg = default_config['influxdb']
    coap_ip = default_config['coap']['ip']
    
    ldr_sensors = []
    for sensor_cfg in sensors_config['sensors']:
        # Extract specific configuration for the current sensor
        sensor_id = sensor_cfg['id']
        coap_cfg = {"coap_ip": coap_ip, "coap_port": sensor_cfg["coap_port"]}
        position = Position(**sensor_cfg['position'])
        plant = Plant(**sensor_cfg['plant'])
        sampling_period = sensor_cfg['sampling_period']
        accum_window = sensor_cfg['accumulation_window']
        
        # Initialize the sensor manager and store in the list
        ldr_sensor = LdrSensorManager(coap_cfg, 
                                      mqtt_cfg, 
                                      influxdb_cfg, 
                                      sensor_id, 
                                      position, 
                                      plant, 
                                      sampling_period)
        ldr_sensor.print_info()
        ldr_sensors.append(ldr_sensor)
    
    return ldr_sensors


async def load_sensors():
    """
    Load sensor configurations and initialize their managers.
    """
    logger.debug("Loading sensors")
    
    global ldr_sensors
    
    # Load configurations
    default_config = await load_default_config()
    sensors_config = await load_sensors_config()
    
    # Setup sensors based on the loaded configurations
    new_sensors = await setup_sensors(default_config, sensors_config)
    ldr_sensors = new_sensors


def check_time():
    """Check the current datetime and return whether the precise hour, quarter of hour or half of hour passed."""
    global last_pred_hour
    global last_pred_min
    now = datetime.now()
    if now.hour in [h for h in range(0, 24, 4) if h!=last_pred_hour] and now.minute in [m for m in [0, 15, 30, 45] if m!= last_pred_min]:
        last_pred_hour = now.hour
        last_pred_min = now.minute
        return True
    else:
        return False
    

def welcome_message() -> None:
    """
    Display a colorful welcome message for the main script.
    """
    welcome = (
        f"{WHITE}==================================================================={BLUE}\n"
        "\n"
        f"                   Welcome to {BOLD}{RED}A{YELLOW}l{LIME}e{CYAN}r{BLUE}t{MAGENTA} U{RED}n{YELLOW}i{LIME}t{WHITE}{BLUE}        \n"
        "\n"
        "\033[3m               The script acts as alert unit.\n"
        f"\n{WHITE}===================================================================\n"
    )
    print(f"{BLUE}{welcome}{WHITE}")

async def main():    
    default_config = await load_default_config()
    influxdb_cfg = default_config['influxdb']
    telegram_cfg = default_config['telegram']
    db_client = DBClient(influxdb_cfg['token'], influxdb_cfg['org'], influxdb_cfg['url'], influxdb_cfg['bucket'])

    global ldr_sensors
    await load_sensors()
    last_current_optimal_sensor = ldr_sensors[0]
    last_future_optimal_sensor = ldr_sensors[0]

    welcome_message()
    while True:
        # The alert is performed any 4h
        if check_time():
            for ldr_sensor in ldr_sensors:
                last_30m_df = db_client.load_timeseries('4h', ldr_sensor.sensor_id)
                next_30m_df = db_client.load_predictions('4h', ldr_sensor.sensor_id)
                if last_30m_df is not None and next_30m_df is not None:
                    ldr_sensor.ldr_timeseries_avg = last_30m_df['y'].mean(skipna=True)
                    logger.info(f"LDR{ldr_sensor.sensor_id}: {ldr_sensor.ldr_timeseries_avg: .2f}")
                    ldr_sensor.predicted_ldr_avg = next_30m_df['y'].mean(skipna=True)
                    logger.info(f"LDR{ldr_sensor.sensor_id} prediction: {ldr_sensor.predicted_ldr_avg: .2f}")
            
            optimal_pos_sensor = max(ldr_sensors, key=lambda ldr_sensor: ldr_sensor.ldr_timeseries_avg)
            optimal_next_pos_sensor = max(ldr_sensors, key=lambda ldr_sensor: ldr_sensor.predicted_ldr_avg)

            if (optimal_pos_sensor.ldr_timeseries_avg > last_current_optimal_sensor.ldr_timeseries_avg + 10) or (optimal_next_pos_sensor.predicted_ldr_avg > last_future_optimal_sensor.predicted_ldr_avg + 10):
                message = (
                    f"LDR{optimal_pos_sensor.sensor_id} ({optimal_pos_sensor.position.name}) has received the highest amount of light in the last 4h.\n"
                    f"LDR{optimal_next_pos_sensor.sensor_id} ({optimal_next_pos_sensor.position.name}) should receive the highest amount of light in the next 4h."
                )

                logger.info(message)
                last_current_optimal_sensor = optimal_pos_sensor
                last_future_optimal_sensor = optimal_next_pos_sensor

                fig, ax = plt.subplots(ncols=1, nrows=len(ldr_sensors), figsize=(10, 3 * len(ldr_sensors)), sharex=True)
                now = datetime.now()

                for ldr_sensor, subplot_ax in zip(ldr_sensors, ax):
                    # Retrieve data for the current sensor
                    last_30m_df = db_client.load_timeseries('4h', ldr_sensor.sensor_id)
                    next_30m_df = db_client.load_predictions('4h', ldr_sensor.sensor_id)
                    if last_30m_df is not None and next_30m_df is not None: 
                        # Plot last 4h and next 4h
                        subplot_ax.plot(last_30m_df['ds'], last_30m_df['y'], label=f"Sensed", color="#03234B", marker='o', mfc='#ffffff', mec='#03234B')
                        subplot_ax.plot(next_30m_df['ds'], next_30m_df['y'], linestyle='--', label=f"Predicted", color="#CC2936", marker='o', mfc='#ffffff', mec='#CC2936')
                        subplot_ax.axvline(now, color='#4EA699', linestyle='--', label=f'Now: {now.strftime("%H:%M")}')
                        subplot_ax.set_ylim(0,100)
                        subplot_ax.legend()
                        
                        # Set titles and labels for this subplot
                        subplot_ax.set_ylabel(f"LDR{ldr_sensor.sensor_id} [%]")
                        subplot_ax.grid(linestyle='--')
                        subplot_ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
                        subplot_ax.xaxis.set_major_locator(mdates.AutoDateLocator())
                
                
                ax[-1].set_xlabel("Time")

                # Adjust layout to prevent overlapping
                fig.tight_layout()

                # Save the plot to an in-memory file
                plot_file = BytesIO()
                plt.savefig(plot_file, format='png')
                plot_file.seek(0)
                plt.close()


                try:
                    bot = telegram.Bot(token=telegram_cfg['token'])
                    # Send the text message
                    await asyncio.create_task(bot.send_message(chat_id=telegram_cfg['chat_id'], text=message))
                    # Send the plot as an image
                    await asyncio.create_task(bot.send_photo(chat_id=telegram_cfg['chat_id'], photo=plot_file))
                except Exception as e:
                    logger.error(f"Exception: {e}")
                finally:
                    plot_file.close()
        sleep(1)


if __name__ == "__main__":
    asyncio.run(main())