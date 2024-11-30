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

import logging
from dataclasses import dataclass, field

@dataclass
class Position():
    """
    Sensor position manager.
    
    This class represents the position of a sensor in a system, allowing for the 
    management and update of position details (ID, name, description) and the 
    association with a sensor. It includes functionality for logging and updating 
    position details.

    Attributes
    ----------
    position_id : str
        Unique identifier for the sensor's position.
    name : str
        The name or label of the position.
    description : str
        A description providing more context about the position.
    sensor_id : str, optional
        The identifier of the sensor associated with this position. Default is an empty string.
    logger : logging.Logger
        Logger used for logging position information and updates.
    
    Methods
    -------
    update(position_id=None, name=None, description=None, sensor_id=None)
        Updates the position details with new values. Only non-None values will be updated.
    print_position()
        Logs the current position details (ID and name).
    """
    
    position_id: str  # Unique identifier for the position
    name: str          # Name of the position (e.g., "Living Room", "Kitchen")
    description: str   # A description of the position
    sensor_id: str = ""  # Optional sensor ID associated with this position
    logger: logging.Logger = field(init=False, default=logging.getLogger('Position'))
    
    def __post_init__(self):
        """
        Initializes the logger for the Position class.
        
        This function is automatically called after the object is initialized
        by the dataclass. It sets the logger level to INFO.
        """
        self.logger.setLevel(logging.INFO)
        
    def update(self, position_id: str = None, name: str = None, description: str = None, sensor_id: str = None) -> None:
        """
        Update the position details with new values if provided.
        
        This method allows you to modify any of the position's attributes
        (position_id, name, description, sensor_id) by passing in new values.
        Only the attributes with non-None values will be updated.
        
        Parameters
        ----------
        position_id : str, optional
            New position ID. If provided, the position ID will be updated.
        name : str, optional
            New name for the position. If provided, the name will be updated.
        description : str, optional
            New description for the position. If provided, the description will be updated.
        sensor_id : str, optional
            New sensor ID associated with the position. If provided, the sensor ID will be updated.
        
        Returns
        ------
        None
            This method does not return anything. It updates the position's attributes in place.
        """
        if position_id:
            self.position_id = position_id
        if name:
            self.name = name
        if description:
            self.description = description
        if sensor_id:
            self.sensor_id = sensor_id
        
    def print_position(self):
        """
        Logs the current position details (position_id and name).
        
        This method is useful for debugging or tracking the position information
        in the system. It logs the position's ID and name to the logger.
        
        Returns
        ------
        None
            This method does not return anything. It only logs the position details.
        """
        self.logger.info(f"position:{self.position_id}:{self.name}")
