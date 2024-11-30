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

import datetime
import logging
import numpy as np
import aiocoap
import aiocoap.resource as resource
from aiocoap import Message
import asyncio

from sensorInfo.plant import Plant
from sensorInfo.position import Position
from comm.mqtt_client import MqttClient
from comm.db_client import DBClient

class LdrSensorManager(resource.Resource):
    """
    A manager class for Light-Dependent Resistor (LDR) sensors. Handles CoAP communication,
    MQTT configuration updates, and InfluxDB storage for time-series data and performance metrics.
    
    Attributes
    ----------
    coap_cfg : dict[str, None]
        Configuration for the CoAP communication protocol (e.g., IP, port).
    mqtt_client : MqttClient
        MQTT client for publishing sensor updates.
    influxdb_client : DBClient
        InfluxDB client for storing time-series data and metrics.
    sensor_id : str
        Unique identifier for the sensor.
    plant : Plant
        Information about the plant associated with the sensor.
    position : Position
        Geographic or logical position of the sensor.
    cs_sampling_period : int
        Current sampling period for CoAP communication (in seconds).
    ns_sampling_period : int
        Updated sampling period, applied dynamically if changed.
    ldr_timeseries : np.array
        Stores the time-series data for LDR values.
    coap_ldr_value : int
        Latest LDR value received via CoAP communication.
    """

    def __init__(self, coap_cfg: dict[str, None], mqtt_cfg: dict[str, None], influxdb_cfg: dict[str, str],
                 sensor_id: str, position: Position, plant: Plant, sampling_period: int) -> None:
        """
        Initializes the LDR Sensor Manager.

        Parameters
        ----------
        coap_cfg : dict[str, None]
            CoAP protocol configuration dictionary.
        mqtt_cfg : dict[str, None]
            MQTT broker configuration dictionary.
        influxdb_cfg : dict[str, str]
            InfluxDB connection configuration dictionary.
        sensor_id : str
            Unique ID for the sensor.
        position : Position
            Sensor's position (e.g., location or identifier).
        plant : Plant
            Information about the associated plant.
        sampling_period : int
            Sampling period in seconds for CoAP communication.
        """
        super().__init__()
        self.logger = logging.getLogger("CoAP")
        self.logger.setLevel(logging.INFO)

        self.put_response_p = "OK"

        self.LDR_start_timeseries = datetime.datetime.now()
        self.coap_cfg = coap_cfg
        self.mqtt_client = MqttClient(mqtt_cfg['ip'], mqtt_cfg['port'], mqtt_cfg['user'], mqtt_cfg['password'],
                                      sensor_id, position, sampling_period)
        self.influxdb_client = DBClient(influxdb_cfg['token'], influxdb_cfg['org'], influxdb_cfg['url'], influxdb_cfg['bucket'])
        self.sensor_id = sensor_id
        self.plant = plant
        self.plant.sensor_id = sensor_id
        self.position = position
        self.position.sensor_id = sensor_id
        self.cs_sampling_period = sampling_period
        self.ns_sampling_period = sampling_period
        self.coap_ldr_value = 0
        self.ldr_timeseries = np.array([], dtype=int)
        self.ldr_timeseries_avg = 0
        self.predicted_ldr_avg = 0

    def print_info(self) -> None:
        """
        Prints basic information about the sensor configuration.
        """
        self.logger.debug(f"ID: {self.sensor_id}, position: {self.position.name}, sampling period: {self.cs_sampling_period}")

    async def render_put(self, request: Message) -> Message:
        """
        Handles CoAP PUT requests for receiving LDR data updates.

        Parameters
        ----------
        request : Message
            Incoming CoAP request.

        Returns
        -------
        response: Message
            Response indicating the request was successfully processed.
        """
        decoded_string = request.payload.decode('utf-8')
        query_params = dict(param.split('=') for param in decoded_string.split('&'))

        sensor_id = query_params.get('sensor_id')
        location = query_params.get('location')
        data = query_params.get('data')
        self.logger.info(f"CoAP message received: ID({sensor_id}) - position({location}) - value({data}%)")

        self.store_value(query_params)
        response = Message(code=aiocoap.CHANGED, payload=self.put_response_p.encode('utf-8'))
        return response

    async def coap_server(self) -> None:
        """
        Starts the CoAP server for handling sensor requests.
        """
        root = resource.Site()
        root.add_resource([".well-known", "core"], resource.WKCResource(root.get_resources_as_linkheader))
        root.add_resource([f"ldrData{self.sensor_id}"], self)

        await aiocoap.Context.create_server_context(root, bind=(self.coap_cfg['coap_ip'], self.coap_cfg['coap_port']))
        await asyncio.get_running_loop().create_future()

    def update_sensor(self, position: Position, sampling_period: int, plant: Plant) -> None:
        """
        Updates the sensor configuration dynamically.

        Parameters
        ----------
        position : Position
            New sensor position.
        sampling_period : int
            New sampling period in seconds.
        plant : Plant
            Updated plant information.
        """
        self.position = position
        self.ns_sampling_period = sampling_period
        self.plant = plant

        self.mqtt_client.update_sensor(position, sampling_period)

    def store_value(self, content: dict[str, str]) -> None:
        """
        Stores the received LDR sensor value and timestamp in the database.

        Parameters
        ----------
        content : dict[str, str]
            Dictionary containing CoAP message parameters.
        """
        self.coap_ldr_value = content.get('data')
        self.influxdb_client.store_value("ldrValue", "ldr", self.sensor_id, self.coap_ldr_value)