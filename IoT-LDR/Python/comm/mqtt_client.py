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
import asyncio
import paho.mqtt.client as mqtt

from sensorInfo import Position


class MqttClient():
    """
    MQTT Client manager for handling the connection and communication with an MQTT broker.
    Publishes sensor configuration updates at regular intervals.
    
    Attributes
    ----------
    logger : logging.Logger
        Logger instance for logging MQTT-related messages.
    mqtt_cfg : dict
        Configuration settings for the MQTT connection, including IP, port, username, password, etc.
    client : mqtt.Client
        The MQTT client instance used to manage the connection.
    sensor_id : str
        The unique identifier for the sensor managed by this client.
    position : Position
        The position of the sensor.
    sampling_period : int
        The sampling period in seconds for data collection.
    """

    def __init__(self, mqtt_ip: str, mqtt_port: int, mqtt_user: str, mqtt_password: str,
                 sensor_id: str, position: Position, sampling_period: int):
        """
        Initializes the MQTT client manager and configures the MQTT connection.

        Parameters
        ----------
        mqtt_ip : str
            The IP address of the MQTT broker.
        mqtt_port : int
            The port number used to connect to the MQTT broker.
        mqtt_user : str
            The username for MQTT broker authentication.
        mqtt_password : str
            The password for MQTT broker authentication.
        sensor_id : str
            The unique ID for the sensor that this client manages.
        position : Position
            The position object representing the sensor's physical or logical location.
        sampling_period : int
            The sampling period in seconds that dictates how often the sensor collects data.
        """
        self.logger = logging.getLogger("MQTT")
        self.logger.setLevel(logging.INFO)

        self.mqtt_cfg = {
            "ip": mqtt_ip,
            "port": mqtt_port,
            "keep_alive": 60,
            "username": mqtt_user,
            "password": mqtt_password
        }
        """MQTT configuration for the node."""
        
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.username_pw_set(self.mqtt_cfg['username'], self.mqtt_cfg['password'])

        self.sensor_id = sensor_id
        self.position = position
        self.sampling_period = sampling_period

    def update_sensor(self, position: Position, sampling_period: int):
        """
        Updates the configuration for the sensor, including position and sampling period.

        Parameters
        ----------
        position : Position
            The new position of the sensor.
        sampling_period : int
            The new sampling period for the sensor.
        """
        self.position = position
        self.sampling_period = sampling_period

    def on_connect(self, client, userdata, flags, rc) -> None:
        """
        Callback function that is called when the client successfully connects to the MQTT broker.

        Parameters
        ----------
        rc : int
            The return code from the broker indicating the connection status.
        """
        self.logger.info(f"Connected to MQTT broker, rc={rc}")

    def mqtt_connect(self) -> None:
        """
        Establishes the connection to the MQTT broker using the configured settings.
        Starts the MQTT client's loop for managing communication.
        """
        self.client.connect(self.mqtt_cfg['ip'], self.mqtt_cfg['port'], self.mqtt_cfg['keep_alive'])
        self.client.loop_start()

    def mqtt_disconnect(self) -> None:
        """
        Disconnects from the MQTT broker and stops the MQTT client's loop.
        """
        self.client.loop_stop()
        self.client.disconnect()

    def mqtt_publish(self, topic: str, payload: None, qos: int = 2) -> None:
        """
        Publishes a message to a specified MQTT topic.

        Parameters
        ----------
        topic : str
            The topic to which the message should be published.
        payload : None
            The content of the message being sent. Can be a string, int, float, or other types.
        qos : int, optional, default: 2
            The Quality of Service level to use for the message (0, 1, or 2).
        """
        self.logger.debug(f"Publishing to topic '{topic}' with payload '{payload}' and QoS {qos}")
        self.client.publish(topic, payload, qos=qos)

    async def periodic_publish(self) -> None:
        """
        Periodically publishes sensor configuration (position and sampling period) to the MQTT broker.
        Runs in an asynchronous loop and publishes every 5 seconds.

        This method connects to the MQTT broker, continuously publishes sensor data, 
        and then disconnects once done.

        Parameters
        ----------
        sensor_id : str
            The sensor's unique identifier to be published.
        sampling_period : int
            The sampling period of the sensor to be published.
        position : Position
            The position of the sensor to be published.
        """
        self.mqtt_connect()
        try:
            while True:
                self.mqtt_publish(f"home/ldr{self.sensor_id}/sampling_period", self.sampling_period)
                self.mqtt_publish(f"home/ldr{self.sensor_id}/position", self.position.name)
                await asyncio.sleep(5)
        finally:
            self.mqtt_disconnect()
