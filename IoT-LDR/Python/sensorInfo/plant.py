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

from dataclasses import dataclass

@dataclass
class Plant():
    """
    A dataclass representing a plant.

    This class holds information about the plant's type, the amount of sunlight it 
    needs (in hours), and the associated sensor ID for monitoring purposes.

    Attributes
    ----------
    type : str
        The type of the plant (e.g., "Cactus", "Fern").
    light_amount : int
        The number of hours the plant needs exposure to sunlight per day.
    sensor_id : str
        The unique identifier for the sensor associated with this plant.

    Methods
    -------
    update_plant(type=None, light_amount=None, sensor_id=None)
        Updates the plant's attributes with the new values provided.
    """

    type: str
    """The type of the plant (e.g., "Cactus", "Fern")"""
    
    light_amount: int
    """The number of hours of sunlight the plant needs per day"""
    
    sensor_id: str
    """The unique identifier for the sensor associated with this plant"""

    def update_plant(self, type: str = None, light_amount: int = None, sensor_id: str = None) -> None:
        """
        Update the plant settings with new values.

        This method allows for updating one or more attributes of the plant object.
        If any of the parameters are provided (i.e., not None), they will update the 
        corresponding attributes of the plant.

        Parameters
        ----------
        type : str, optional
            The new type of the plant (e.g., "Cactus", "Fern"). Defaults to None.
        light_amount : int, optional
            The new number of hours the plant requires exposure to sunlight. Defaults to None.
        sensor_id : str, optional
            The new sensor ID associated with the plant. Defaults to None.

        Returns
        -------
        None
            This method updates the plant attributes in place and does not return any value.
        """
        if type:
            self.type = type
        if light_amount:
            self.light_amount = light_amount
        if sensor_id:
            self.sensor_id = sensor_id
