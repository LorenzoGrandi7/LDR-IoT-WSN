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
import json
import logging
from watchdog.observers import Observer

from comm import *  # Communication-related utilities (e.g., MQTT or CoAP handling)
from tools import *  # General utility functions for the script
from sensorInfo import *  # Sensor-specific information and classes

# Initialize logger for the data proxy
logger = logging.getLogger("data proxy")
logger.setLevel(logging.INFO)

# ANSI color codes for terminal output
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

async def load_sensors() -> None:
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

async def reload_sensors() -> None:
    """
    Reload sensor configurations, updating existing sensors or adding new ones.
    """
    logger.debug("Reloading sensors")
    
    global ldr_sensors
    
    try:
        # Reload configurations
        default_config = await load_default_config()
        sensors_config = await load_sensors_config()
        
        for sensor_cfg in sensors_config['sensors']:
            sensor_id = sensor_cfg['id']
            
            # Check if the sensor already exists in the current list
            existing_sensor: LdrSensorManager = next((ldr for ldr in ldr_sensors if ldr.sensor_id == sensor_id), None)
                
            if existing_sensor:
                # Update the existing sensor's configuration
                existing_sensor.update_sensor(Position(**sensor_cfg['position']), 
                                              sensor_cfg['sampling_period'],
                                              Plant(**sensor_cfg['plant']))
                logger.debug(f"Updated sensor {sensor_id} with new config.")
                existing_sensor.print_info()
            else:
                # Add a new sensor if not already present
                coap_cfg = {"coap_ip": default_config['coap']['ip'], "coap_port": sensor_cfg["coap_port"]}
                mqtt_cfg = default_config['mqtt']
                influxdb_cfg = default_config['influxdb']
                
                new_sensor = LdrSensorManager(coap_cfg, 
                                              mqtt_cfg, 
                                              influxdb_cfg, 
                                              sensor_id, 
                                              Position(**sensor_cfg['position']), 
                                              Plant(**sensor_cfg['plant']), 
                                              sensor_cfg['sampling_period']
                                              )
                ldr_sensors.append(new_sensor)
                logger.debug(f"Added new sensor {sensor_id}.")
    finally:
        logger.debug("Final configuration state.")

def welcome_message() -> None:
    """
    Display a colorful welcome message for the main script.
    """
    welcome = (
        f"{WHITE}==================================================================={BLUE}\n"
        "\n"
        f"                   Welcome to {BOLD}{RED}S{YELLOW}e{LIME}n{CYAN}s{BLUE}o{MAGENTA}r {RED}P{YELLOW}r{LIME}o{CYAN}x{BLUE}{MAGENTA}y{WHITE}{BLUE}        \n"
        "\n"
        "\033[3mThe script acts as a proxy between the sensors and the database.\n"
        f"To manage the sensors run cli.py.{WHITE}\n"
        f"\n===================================================================\n"
    )
    print(f"{BLUE}{welcome}{WHITE}")

async def main() -> None:
    """
    Main function to manage the sensor proxy. It handles:
    - Loading initial sensor configurations.
    - Running CoAP servers and MQTT publishers for the sensors.
    - Monitoring configuration file changes for dynamic updates.
    """
    welcome_message()
    
    global ldr_sensors
    
    # Load sensors
    await load_sensors()
    
    # Setup file watcher for dynamic configuration reloads
    loop = asyncio.get_event_loop()
    event_handler = ConfigFileHandler(loop, reload_sensors)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    
    # Main loop to handle CoAP and MQTT functionality
    while True:
        try:
            await asyncio.gather(
                *[ldr.coap_server() for ldr in ldr_sensors],  # Start CoAP servers
                *[ldr.mqtt_client.periodic_publish() for ldr in ldr_sensors],  # Start periodic MQTT publishing
                reload_sensors()  # Periodically reload configurations
            )
        except Exception as e:
            logger.error(f"Error occurred: {e}")
        finally:
            observer.stop()
            observer.join()

if __name__ == "__main__":
    asyncio.run(main())
