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
import time
import asyncio
from datetime import datetime
import pytz
import numpy as np
import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

class DBClient:
    """
    Manages interactions with an InfluxDB database, including storing and retrieving
    sensor data, managing time series, and handling predictions.

    Attributes
    ----------
    tz : pytz.timezone
        Timezone for data storage and retrieval, set to "Europe/Rome".

    Methods
    -------
    store_value(measurement, field, sensor_id, value)
        Store a single value in the InfluxDB database.
    store_ldr_influxdb(ldr_value, sensor_id)
        Store an LDR (Light Dependent Resistor) sensor value in the database.
    store_mean_lat_influxdb(mean_lat, sensor_id)
        Store mean latency values in the database.
    load_timeseries(time_window, sensor_id)
        Retrieve a time series of sensor data from the database.
    store_predictions(predictions_df, sensor_id)
        Store predicted values in the database.
    """
    
    tz = pytz.timezone("Europe/Rome")

    def __init__(self, db_token: str, db_org: str, db_url: str, db_bucket: str):
        """
        Initialize the InfluxDB client with configuration settings.

        Parameters
        ----------
        db_token : str
            Authentication token for the InfluxDB instance.
        db_org : str
            Organization name for the InfluxDB instance.
        db_url : str
            URL of the InfluxDB instance.
        db_bucket : str
            Bucket (database) name where data will be stored.
        """
        self.logger = logging.getLogger("InfluxDB")
        self.logger.setLevel(logging.INFO)

        # Database configuration
        self.db_cfg = {
            "token": db_token,
            "org": db_org,
            "url": db_url,
            "bucket": db_bucket
        }

    def store_value(self, measurement: str, field: str, sensor_id: str, value: float) -> None:
        """
        Store a single measurement value in the InfluxDB database.

        Parameters
        ----------
        measurement : str
            Name of the measurement (e.g., sensor type).
        field : str
            Field name under which the value is stored.
        sensor_id : str
            Identifier for the sensor.
        value : float
            The value to store.
        """
        try:
            self.logger.debug(f"Storing value from {sensor_id} in {measurement}: {value}")
            client = InfluxDBClient(url=self.db_cfg['url'], token=self.db_cfg['token'], org=self.db_cfg['org'])
            write_api = client.write_api(write_options=SYNCHRONOUS)

            # Create a point with the given data
            p = Point(measurement).tag("sensor", sensor_id).field(field, float(value)).time(datetime.now(tz=self.tz), WritePrecision.S)
            self.logger.debug(f"Point: {p}")
            
            # Write the point to the database
            write_api.write(bucket=self.db_cfg['bucket'], org=self.db_cfg['org'], record=p)
            client.close()
        except Exception as e:
            self.logger.error(f"Exception: {e}")

    def store_ldr_influxdb(self, ldr_value: float, sensor_id: str) -> None:
        """
        Store an LDR sensor value in the InfluxDB database.

        Parameters
        ----------
        ldr_value : float
            The light intensity value measured by the LDR sensor.
        sensor_id : str
            Identifier for the sensor.
        """
        try:
            self.logger.debug(f"Storing values sensed from LDR{sensor_id}: {ldr_value}")
            client = InfluxDBClient(url=self.db_cfg['url'], token=self.db_cfg['token'], org=self.db_cfg['org'])
            write_api = client.write_api(write_options=SYNCHRONOUS)

            # Store LDR value as a "ldrValue" measurement
            p = Point("ldrValue").tag("sensor", sensor_id).field("ldr", float(ldr_value)).time(datetime.now(tz=self.tz), WritePrecision.S)
            write_api.write(bucket=self.db_cfg['bucket'], org=self.db_cfg['org'], record=p)
            client.close()
        except Exception as e:
            self.logger.error(f"Exception: {e}")

    def store_mean_lat_influxdb(self, mean_lat: float, sensor_id: str) -> None:
        """
        Store the mean latency value in the InfluxDB database.

        Parameters
        ----------
        mean_lat : float
            Mean latency to store.
        sensor_id : str
            Identifier for the sensor.
        """
        try:
            self.logger.debug(f"Storing mean latency for LDR{sensor_id}: {mean_lat}")
            client = InfluxDBClient(url=self.db_cfg['url'], token=self.db_cfg['token'], org=self.db_cfg['org'])
            write_api = client.write_api(write_options=SYNCHRONOUS)

            # Store the mean latency value as a "meanLat" measurement
            p = Point("meanLat").tag("sensor", sensor_id).field("mean_lat", float(mean_lat)).time(datetime.now(tz=self.tz), WritePrecision.S)
            write_api.write(bucket=self.db_cfg['bucket'], org=self.db_cfg['org'], record=p)
            client.close()
        except Exception as e:
            self.logger.error(f"Exception: {e}")

    def load_timeseries(self, time_window: str, sensor_id: str) -> pd.DataFrame:
        """
        Load a time series of the last `time_window` samples for a given sensor.

        Parameters
        ----------
        time_window : str
            The time range to fetch data (e.g., '1h', '7d').
        sensor_id : str
            Identifier for the sensor.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the time series data with columns `ds` (timestamps)
            and `y` (values). If insufficient data is available, returns an empty DataFrame.
        """
        try:
            client = InfluxDBClient(url=self.db_cfg['url'], token=self.db_cfg['token'], org=self.db_cfg['org'])

            # Query InfluxDB for the specified time window and sensor
            query = f'''
                from(bucket: "{self.db_cfg['bucket']}")
                    |> range(start: -{time_window}, stop: now())
                    |> filter(fn: (r) =>
                        r._measurement == "ldrValue" and
                        r._field == "ldr" and
                        r.sensor == "{sensor_id}"
                    )
                '''
            query_api = client.query_api()
            result = query_api.query(query)

            # Parse results into a DataFrame
            data = {'ds': [], 'y': []}
            for table in result:
                for record in table.records:
                    data['ds'].append(record.get_time())
                    data['y'].append(record.get_value())

            df = pd.DataFrame(data)
            df['ds'] = pd.to_datetime(df['ds']).dt.tz_convert('Europe/Rome').dt.tz_localize(None)

            # Validate if data is sufficient
            if df.dropna().shape[0] < 2:
                df = pd.DataFrame(columns=['ds', 'y'])
            else:
                self.logger.debug("Sufficient data found. Proceeding to analysis")
            
            client.close()
            return df
        except Exception as e:
            self.logger.error(f"Exception: {e}")

    def store_predictions(self, predictions_df: pd.DataFrame, sensor_id: str) -> None:
        """
        Store predicted values in the InfluxDB database.

        Parameters
        ----------
        predictions_df : pd.DataFrame
            DataFrame containing predicted values with columns `ds` (timestamps)
            and `yhat` (predicted values).
        sensor_id : str
            Identifier for the sensor.
        """
        try:
            self.logger.debug(f"Storing predicted values for LDR{sensor_id}")
            client = InfluxDBClient(url=self.db_cfg['url'], token=self.db_cfg['token'], org=self.db_cfg['org'])
            write_api = client.write_api(write_options=SYNCHRONOUS)

            # Write predictions row by row to the database
            for _, row in predictions_df.iterrows():
                timestamp = pd.to_datetime(row['ds']).tz_localize('Europe/Rome')
                p = Point("ldrValue").tag("sensor", sensor_id).field("pred", float(row['yhat'])).time(timestamp, WritePrecision.S)
                write_api.write(bucket=self.db_cfg['bucket'], org=self.db_cfg['org'], record=p)
            
            client.close()
        except Exception as e:
            self.logger.error(f"Exception: {e}")

    def store_predictions_upper(self, predictions_df: pd.DataFrame, sensor_id: str) -> None:
        """
        Store predicted values in the InfluxDB database.

        Parameters
        ----------
        predictions_df : pd.DataFrame
            DataFrame containing predicted values with columns `ds` (timestamps)
            and `yhat` (predicted values).
        sensor_id : str
            Identifier for the sensor.
        """
        try:
            self.logger.debug(f"Storing predicted values for LDR{sensor_id}")
            client = InfluxDBClient(url=self.db_cfg['url'], token=self.db_cfg['token'], org=self.db_cfg['org'])
            write_api = client.write_api(write_options=SYNCHRONOUS)

            # Write predictions row by row to the database
            for _, row in predictions_df.iterrows():
                timestamp = pd.to_datetime(row['ds']).tz_localize('Europe/Rome')
                p = Point("ldrValue").tag("sensor", sensor_id).field("pred_upper", float(row['yhat_upper'])).time(timestamp, WritePrecision.S)
                write_api.write(bucket=self.db_cfg['bucket'], org=self.db_cfg['org'], record=p)
            
            client.close()
        except Exception as e:
            self.logger.error(f"Exception: {e}")

    def store_predictions_lower(self, predictions_df: pd.DataFrame, sensor_id: str) -> None:
        """
        Store predicted values in the InfluxDB database.

        Parameters
        ----------
        predictions_df : pd.DataFrame
            DataFrame containing predicted values with columns `ds` (timestamps)
            and `yhat` (predicted values).
        sensor_id : str
            Identifier for the sensor.
        """
        try:
            self.logger.debug(f"Storing predicted values for LDR{sensor_id}")
            client = InfluxDBClient(url=self.db_cfg['url'], token=self.db_cfg['token'], org=self.db_cfg['org'])
            write_api = client.write_api(write_options=SYNCHRONOUS)

            # Write predictions row by row to the database
            for _, row in predictions_df.iterrows():
                timestamp = pd.to_datetime(row['ds']).tz_localize('Europe/Rome')
                p = Point("ldrValue").tag("sensor", sensor_id).field("pred_lower", float(row['yhat_lower'])).time(timestamp, WritePrecision.S)
                write_api.write(bucket=self.db_cfg['bucket'], org=self.db_cfg['org'], record=p)
            
            client.close()
        except Exception as e:
            self.logger.error(f"Exception: {e}")

    def load_predictions(self, time_window: str, sensor_id: str) -> pd.DataFrame:
        """
        Load a time series of the next `time_window` predicted samples for a given sensor.

        Parameters
        ----------
        time_window : str
            The time range to fetch data (e.g., '1h', '7d').
        sensor_id : str
            Identifier for the sensor.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the time series data with columns `ds` (timestamps)
            and `y` (values). If insufficient data is available, returns an empty DataFrame.
        """
        try:
            client = InfluxDBClient(url=self.db_cfg['url'], token=self.db_cfg['token'], org=self.db_cfg['org'])

            # Query InfluxDB for the specified time window and sensor
            query = f'''
                import "experimental"
                from(bucket: "{self.db_cfg['bucket']}")
                    |> range(start: now(), stop: experimental.addDuration(d: {time_window}, to: now()))
                    |> filter(fn: (r) =>
                        r._measurement == "ldrValue" and
                        r._field == "pred" and
                        r.sensor == "{sensor_id}"
                    )
                '''
            query_api = client.query_api()
            result = query_api.query(query)

            # Parse results into a DataFrame
            data = {'ds': [], 'y': []}
            for table in result:
                for record in table.records:
                    data['ds'].append(record.get_time())
                    data['y'].append(record.get_value())

            df = pd.DataFrame(data)
            df['ds'] = pd.to_datetime(df['ds']).dt.tz_convert('Europe/Rome').dt.tz_localize(None)

            # Validate if data is sufficient
            if df.dropna().shape[0] < 2:
                df = pd.DataFrame(columns=['ds', 'y'])
            else:
                self.logger.debug("Sufficient data found. Proceeding to analysis")
            
            client.close()
            return df
        except Exception as e:
            self.logger.error(f"Exception: {e}")