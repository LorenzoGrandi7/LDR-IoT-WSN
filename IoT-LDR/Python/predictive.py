"""
Predictive Unit for IoT Sensor Data
Author: Lorenzo Grandi
License: Apache License, Version 2.0
"""

import asyncio
import json
import logging
from datetime import datetime

from comm import LdrSensorManager, model_predict, generate_holidays
from sensorInfo import *
from tools import *

# ANSI color codes for terminal output
WHITE = "\033[0m"
RED = "\033[31m"
YELLOW = "\033[33m"
LIME = "\033[32m"
CYAN = "\033[36m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
BOLD = "\033[1m"

# Initialize logger for the predictive unit
logger = logging.getLogger('predictive unit')
logger.setLevel(logging.INFO)

current_holidays = None
last_holiday_day = -1
last_pred_hour: int = -1
last_pred_min: int = -1

async def load_default_config() -> dict:
    """
    Load default configurations from the JSON file.
    
    Returns
    -------
    dict
        Dictionary containing the default configurations.
    """
    logger.debug("Loading default configurations")
    with open(r'.\default_config.json', 'r') as f:
        return json.load(f)
    
async def load_sensors_config() -> dict:
    """
    Load sensors configurations from the JSON file.
    
    Returns
    -------
    dict
        Dictionary containing the sensor configurations.
    """
    logger.debug("Loading sensors configurations")
    with open(r'.\sensors_config.json', 'r') as f:
        return json.load(f)
    
async def load_sensors():
    """
    Load configurations and initialize sensors.
    """
    logger.debug("Loading sensors")
    global ldr_sensors
    
    default_config = await load_default_config()
    sensors_config = await load_sensors_config()
    
    # Initialize sensors
    new_sensors = await setup_sensors(default_config, sensors_config)
    ldr_sensors = new_sensors
    
async def setup_sensors(default_config: dict, sensors_config: dict) -> list[LdrSensorManager]:
    """
    Set up LDR sensors based on configurations.

    Parameters
    ----------
    default_config : dict
        Default configurations.
    sensors_config : dict
        Sensor-specific configurations.

    Returns
    -------
    list
        List of initialized `LdrSensorManager` objects.
    """
    logger.debug("Setting up LDR sensors")
    
    mqtt_cfg = default_config['mqtt']
    influxdb_cfg = default_config['influxdb']
    coap_ip = default_config['coap']['ip']
    
    ldr_sensors = []
    for sensor_cfg in sensors_config['sensors']:
        # Extract configuration details
        sensor_id = sensor_cfg['id']
        coap_cfg = {"coap_ip": coap_ip, "coap_port": sensor_cfg["coap_port"]}
        position = Position(**sensor_cfg['position'])
        plant = Plant(**sensor_cfg['plant'])
        sampling_period = sensor_cfg['sampling_period']
        
        # Initialize sensor manager
        ldr_sensor = LdrSensorManager(coap_cfg, mqtt_cfg, influxdb_cfg, 
                                      sensor_id, position, plant, 
                                      sampling_period)
        ldr_sensor.print_info()
        ldr_sensors.append(ldr_sensor)
    return ldr_sensors

def update_holidays():
    global current_holidays
    global last_holiday_day

    now = datetime.now()
    hours = now.hour
    minutes = now.minute
    # Update holidays once every day at midnight
    if hours == 0 and minutes == 0 and now.day != last_holiday_day:
        last_holiday_day = hours
        current_holidays = generate_holidays(now.year, now.year + 1)
        logger.critical("Updating holidays")
        

async def reload_sensors():
    """
    Reload sensor configurations and update their instances.
    """
    logger.debug("Reloading sensors")
    global ldr_sensors
    
    try:
        # Load updated configurations
        default_config = await load_default_config()
        sensors_config = await load_sensors_config()
        
        for sensor_cfg in sensors_config['sensors']:
            sensor_id = sensor_cfg['id']
            existing_sensor = next((ldr for ldr in ldr_sensors if ldr.sensor_id == sensor_id), None)
            
            if existing_sensor:
                # Update the existing sensor
                existing_sensor.update_sensor(Position(**sensor_cfg['position']), 
                                              sensor_cfg['sampling_period'], 
                                              Plant(**sensor_cfg['plant']))
                logger.debug(f"Updated sensor {sensor_id} with new config.")
                existing_sensor.print_info()
            else:
                # Add a new sensor if it doesn't exist
                coap_cfg = {"coap_ip": default_config['coap']['ip'], "coap_port": sensor_cfg["coap_port"]}
                mqtt_cfg = default_config['mqtt']
                influxdb_cfg = default_config['influxdb']
                
                new_sensor = LdrSensorManager(coap_cfg, mqtt_cfg, influxdb_cfg, 
                                              sensor_id, Position(**sensor_cfg['position']), 
                                              Plant(**sensor_cfg['plant']), 
                                              sensor_cfg['sampling_period'])
                ldr_sensors.append(new_sensor)
                logger.debug(f"Added new sensor {sensor_id}.")
    finally:
        logger.debug("Sensor configuration reloaded.")


def check_time():
    """Change of the hour detector.

    Returns:
        bool: Whether the hour change.
    """
    global last_pred_hour
    global last_pred_min
    now = datetime.now()
    if now.hour in [h for h in range(0, 24) if h != last_pred_hour] and now.minute in [m for m in [0, 15, 30, 45] if m!= last_pred_min]:
        last_pred_hour = now.hour
        last_pred_min = now.min
        return True
    else:
        return False

def welcome_message() -> None:
    """
    Display a colorful welcome message for the predictive unit script.
    """
    welcome = (
        f"{WHITE}==================================================================={BLUE}\n"
        "\n"
        f"                   Welcome to {BOLD}{RED}P{YELLOW}r{LIME}e{CYAN}d{BLUE}i{MAGENTA}c{RED}t{YELLOW}i{LIME}v{CYAN}e{BLUE} U{MAGENTA}n{RED}i{YELLOW}t{WHITE}\n"
        "\n"
        f"{BLUE}This script provides predictive analysis of sensor data.{WHITE}\n"
        f"\n===================================================================\n"
    )
    print(f"{BLUE}{welcome}{WHITE}")


async def main():
    """
    Main function:
    - Periodically gathers recent sensor data (3 hours).
    - Predicts the next hour's data using a predefined model.
    - Reloads sensor configurations periodically.
    """
    global ldr_sensors
    global current_holidays

    # Load default configurations
    default_config = await load_default_config()
    influxdb_cfg = default_config['influxdb']
    
    # Initialize sensors
    await load_sensors()
    current_holidays = generate_holidays(datetime.now().year, datetime.now().date().year + 1)

    welcome_message()
    
    while True:
        while current_holidays is None:
            await asyncio.sleep(1)  # wait for holidays to be initialized

        # Perform in parallel prediction for each sensor
        if check_time():
            await asyncio.gather(*[asyncio.to_thread(model_predict, ldr_sensor, influxdb_cfg, current_holidays) for ldr_sensor in ldr_sensors])
        
        # Reload sensor configurations to reflect updates
        await reload_sensors()
        update_holidays()
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())