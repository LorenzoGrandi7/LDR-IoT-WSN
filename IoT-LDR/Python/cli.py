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

import argparse
import json
import os

# Color codes for terminal output
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

def load_default_config() -> dict:
    """Load default configurations from JSON."""
    config_file = 'default_config.json'
    if not os.path.exists(config_file):
        print(f"Default configuration file '{config_file}' not found.")
        return {}
    
    with open(config_file, 'r') as file:
        return json.load(file)

def load_sensor_config() -> dict:
    """Load sensor configurations from JSON."""
    config_file = 'sensors_config.json'
    if not os.path.exists(config_file):
        print(f"Sensor configuration file '{config_file}' not found.")
        return {}
    
    with open(config_file, 'r') as file:
        return json.load(file)

def save_sensor_config(config: dict) -> None:
    """
    Save sensor configurations to JSON.
    
    Parameters
    ---------
    **config**: dict 
        Configuration dictionary.
    """
    config_file = 'sensors_config.json'
    with open(config_file, 'w') as file:
        json.dump(config, file, indent=4)

def load_position_config() -> dict:
    """Load position configurations from JSON."""
    config_file = 'positions.json'
    if not os.path.exists(config_file):
        print(f"Position configuration file '{config_file}' not found.")
        return {}
    
    with open(config_file, 'r') as file:
        return json.load(file)

def save_position_config(config: dict) -> None:
    """Save position configurations to JSON."""
    config_file = 'positions.json'
    with open(config_file, 'w') as file:
        json.dump(config, file, indent=4)

def get_or_create_position(position_name: str) -> dict:
    """Get a position by name or create a new one if it doesn't exist."""
    config = load_position_config()
    positions = config.get("positions", [])

    # Check if the position already exists
    position = next((p for p in positions if p.get('name') == position_name), None)
    
    if position:
        print(f"Using existing position: {position_name}")
    else:
        print(f"Position '{position_name}' not found. Creating new position.")
        
        # Determine the highest position_id in the current list of positions
        if positions:
            max_position_id = max(int(p.get('position_id', 0)) for p in positions)
        else:
            max_position_id = 0

        # Generate a new position ID
        new_position_id = max_position_id + 1
        
        description = input(f"{YELLOW}\nEnter position description: {WHITE}")
        position = {
            'position_id': str(new_position_id),
            'name': position_name,
            'description': description
        }
        positions.append(position)
        config['positions'] = positions
        save_position_config(config)
        print(f"Created new position: {position_name} with ID {new_position_id}")
    
    return position

def show_sensor(args) -> None:
    """Show sensor information."""
    config = load_sensor_config()
    sensors = config.get("sensors", [])

    if args.id:
        sensor = next((s for s in sensors if s.get("id") == args.id), None)
        if sensor:
            print(f"{BOLD}{CYAN}Sensor ID: {WHITE}{sensor.get('id')}{WHITE}")
            print(f"{BOLD}{CYAN}Position Name: {WHITE}{sensor.get('position', {}).get('name')}{WHITE}")
            print(f"{BOLD}{CYAN}Position Description: {WHITE}{sensor.get('position', {}).get('description')}{WHITE}")
            print(f"{BOLD}{CYAN}Plant Type: {WHITE}{sensor.get('plant', {}).get('type')}{WHITE}")
            print(f"{BOLD}{CYAN}Plant Light Amount: {WHITE}{sensor.get('plant', {}).get('light_amount')}H{WHITE}")
            print(f"{BOLD}{CYAN}Sampling period: {WHITE}{sensor.get('sampling_period')}s{WHITE}")
            print(f"{BOLD}{BLACK}COAP Port: {WHITE}{BLACK}{sensor.get('coap_port')}{WHITE}")
            print(f"=============")
        else:
            print(f"{BOLD}{RED}No sensor found with ID {args.id}{WHITE}")
    else:
        if not sensors:
            print(f"{BOLD}{RED}No sensors found.{WHITE}")
            return
        for sensor in sensors:
            print(f"{BOLD}{CYAN}Sensor ID: {WHITE}{sensor.get('id')}{WHITE}")
            print(f"{BOLD}{CYAN}Position Name: {WHITE}{sensor.get('position', {}).get('name')}{WHITE}")
            print(f"{BOLD}{CYAN}Position Description: {WHITE}{sensor.get('position', {}).get('description')}{WHITE}")
            print(f"{BOLD}{CYAN}Plant Type: {WHITE}{sensor.get('plant', {}).get('type')}{WHITE}")
            print(f"{BOLD}{CYAN}Plant Light Amount: {WHITE}{sensor.get('plant', {}).get('light_amount')}H{WHITE}")
            print(f"{BOLD}{CYAN}Sampling Period: {WHITE}{sensor.get('sampling_period')}s{WHITE}")
            print(f"{BOLD}{BLACK}COAP Port: {WHITE}{BLACK}{sensor.get('coap_port')}{WHITE}")
            print(f"=============")

def add_sensor(args) -> None:
    """Add sensor to configuration."""
    config = load_sensor_config()
    sensors = config.get("sensors", [])
    
    position = get_or_create_position(args.position_name) if args.position_name else {}
    
    new_sensor = {
        'id': args.id,
        'coap_port': args.coap_port if args.coap_port is not None else 0,
        'position': position,
        'plant': {
            'type': args.plant_type if args.plant_type else '',
            'light_amount': args.light_amount if args.light_amount is not None else 10,
            'sensor_id': args.id
        },
        'sampling_period': args.sampling_period if args.sampling_period is not None else 60,
        'accumulation_window': args.accumulation_window if args.accumulation_window is not None else 30
    }
    
    sensors.append(new_sensor)
    config['sensors'] = sensors
    save_sensor_config(config)
    
    print(f"Added new sensor with ID {args.id}")

def update_sensor(args) -> None:
    """Update sensor in configuration."""
    config = load_sensor_config()
    sensors = config.get("sensors", [])
    
    sensor = next((s for s in sensors if s.get('id') == args.id), None)
    if sensor:
        if args.port is not None:
            sensor['coap_port'] = args.port
        if args.position:
            position = get_or_create_position(args.position)
            sensor['position'] = position
        if args.plant:
            sensor['plant']['type'] = args.plant
        if args.light is not None:
            sensor['plant']['light_amount'] = args.light
        if args.period is not None:
            sensor['period'] = args.period
        if args.mean_period is not None:
            sensor['mean-period'] = args.mean_period
        
        save_sensor_config(config)
        
        print(f"Updated sensor with ID {args.id}")
    else:
        print(f"{BOLD}{RED}No sensor found with ID {args.id}{WHITE}")

def update_all_sampling_periods(args) -> None:
    """Update sampling period for all sensors in the configuration."""
    config = load_sensor_config()
    sensors = config.get("sensors", [])
    
    if not sensors:
        print(f"{BOLD}{RED}No sensors found.{WHITE}")
        return

    sampling_period = args.sampling_period
    if sampling_period is not None:
        for sensor in sensors:
            sensor['sampling_period'] = sampling_period
        
        save_sensor_config(config)
        
        print(f"Updated sampling period for all sensors to {sampling_period}")
    else:
        print(f"{BOLD}{RED}No sampling period provided.{WHITE}")

def update_all_accumulation_windows(args) -> None:
    """Update accumulation window for all sensors in the configuration."""
    config = load_sensor_config()
    sensors = config.get("sensors", [])
    
    if not sensors:
        print(f"{BOLD}{RED}No sensors found.{WHITE}")
        return

    accumulation_window = args.accumulation_window
    if accumulation_window is not None:
        for sensor in sensors:
            sensor['accumulation_window'] = accumulation_window
        
        save_sensor_config(config)
        
        print(f"Updated accumulation window for all sensors to {accumulation_window} seconds")
    else:
        print(f"{BOLD}{RED}No accumulation window provided.{WHITE}")
        
def delete_sensor(args) -> None:
    """Delete a specific sensor by ID."""
    config = load_sensor_config()
    sensors = config.get("sensors", [])

    if args.id:
        # Delete sensor by ID
        sensor = next((s for s in sensors if s.get('id') == args.id), None)
        if sensor:
            sensors.remove(sensor)
            config['sensors'] = sensors
            save_sensor_config(config)
            print(f"{BOLD}{RED}Sensor with ID {args.id} has been deleted.{WHITE}")
        else:
            print(f"{BOLD}{RED}No sensor found with ID {args.id}{WHITE}")
    else:
        print(f"{BOLD}{RED}Please specify a sensor ID.{WHITE}")


def show_help() -> None:
    """Show help message."""
    help_message = (
        f"{LIME}  show {MAGENTA}[--id ID] {WHITE}                Show sensor details or all sensors if no ID is provided\n"
        f"{LIME}  add {MAGENTA}--id ID [--port PORT] [--position NAME] [--plant TYPE] [--light AMOUNT] [--period period] [--mean-period WINDOW]\n"
        f"                                  {WHITE}Add a new sensor with the specified details. Only --id is required.\n"
        f"{LIME}  update {MAGENTA}--id ID [--port PORT] [--position NAME] [--plant TYPE] [--light AMOUNT] [--period period] [--mean-period WINDOW]\n"
        f"                                  {WHITE}Update an existing sensor with the specified details. Only --id is required.\n"
        f"{LIME}  period {MAGENTA}period                       {WHITE}Update the sampling period {YELLOW}(in seconds!){WHITE} for all existing sensors.\n"
        f"{LIME}  window {MAGENTA}WINDOW                   {WHITE}Update the time period {YELLOW}(in minutes!){WHITE} for mean computation for all existing sensors.\n"
        f"{LIME}  delete {MAGENTA}--id ID      {WHITE}            Delete the specified sensor.\n"
        f"{LIME}  help                            {WHITE}Show this help message.\n"
        f"{LIME}  exit                            {WHITE}Exit the CLI.\n"
    )
    print(f"{help_message}{WHITE}")

def welcome_interface() -> None:
    """Show welcome message."""
    welcome_message = (
        f"{WHITE}============================================================={BLUE}\n"
        "\n"
        f"               Welcome to {BOLD}{RED}S{YELLOW}e{LIME}n{CYAN}s{BLUE}o{MAGENTA}r {RED}C{YELLOW}L{LIME}I {WHITE}{BLUE}Tool{WHITE}{BLUE}        \n"
        "\n"
        f"{ITALIC}The CLI helps to configure and update the sensors.\n"
        "Type 'help' to see available commands or 'exit' to quit.\n"
        f"\n{WHITE}=============================================================\n"
    )
    
    print(f"{BOLD}{BLUE}{welcome_message}{WHITE}")

def main():
    welcome_interface()
    parser = argparse.ArgumentParser(description="CLI for managing sensor configurations")
    subparsers = parser.add_subparsers()

    # Subparser for showing sensors
    show_parser = subparsers.add_parser("show", help="Show sensor details or all sensors")
    show_parser.add_argument("--id", help="ID of the sensor to show")
    show_parser.set_defaults(func=show_sensor)

    # Subparser for adding sensors
    add_parser = subparsers.add_parser("add", help="Add a new sensor")
    add_parser.add_argument("--id", required=True, help="Sensor ID")
    add_parser.add_argument("--port", type=int, help="COAP port")
    add_parser.add_argument("--position", help="Position name")
    add_parser.add_argument("--plant", help="Plant type")
    add_parser.add_argument("--light", type=int, help="Light amount")
    add_parser.add_argument("--period", type=int, help="Sampling period")
    add_parser.add_argument("--mean-period", type=int, help="Accumulation window in seconds")
    add_parser.set_defaults(func=add_sensor)

    # Subparser for updating sensors
    update_parser = subparsers.add_parser("update", help="Update an existing sensor")
    update_parser.add_argument("--id", required=True, help="Sensor ID")
    update_parser.add_argument("--port", type=int, help="COAP port")
    update_parser.add_argument("--position", help="Position name")
    update_parser.add_argument("--plant", help="Plant type")
    update_parser.add_argument("--light", type=int, help="Light amount")
    update_parser.add_argument("--period", type=int, help="Sampling period")
    update_parser.add_argument("--mean-period", type=int, help="Accumulation window in seconds")
    update_parser.set_defaults(func=update_sensor)

    # Subparser for updating sampling period of all sensors
    update_all_parser = subparsers.add_parser("period", help="Update sampling period for all sensors")
    update_all_parser.add_argument("sampling_period", type=int, help="New sampling period for all sensors")
    update_all_parser.set_defaults(func=update_all_sampling_periods)

    # Subparser for updating accumulation window of all sensors
    update_window_parser = subparsers.add_parser("window", help="Update accumulation window for all sensors")
    update_window_parser.add_argument("accumulation_window", type=int, help="New accumulation window for all sensors in seconds")
    update_window_parser.set_defaults(func=update_all_accumulation_windows)
    
    # Delete sensor
    parser_delete = subparsers.add_parser('delete', help='Delete a sensor by ID or delete all sensors')
    parser_delete.add_argument('--id', type=str, help='Sensor ID to delete')
    parser_delete.set_defaults(func=delete_sensor)

    # Custom help command
    parser.add_argument("command", choices=["help", "exit"], nargs="?")
    
    while True:
        user_input = input(f"{YELLOW}\n> {WHITE}")
        if user_input == "exit":
            print(f"{BLUE}\nExiting CLI. {BOLD}{RED}G{YELLOW}o{LIME}o{CYAN}d{BLUE}b{MAGENTA}y{RED}e{WHITE}!\n")
            break
        elif user_input == "help":
            show_help()
        else:
            try:
                args = parser.parse_args(user_input.split())
                if hasattr(args, 'func'):
                    args.func(args)
                else:
                    show_help()
            except SystemExit:
                pass

if __name__ == "__main__":
    main()
