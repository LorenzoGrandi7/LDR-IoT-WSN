# IoT System for Tracking Daily Light Exposure of Plants

## Objective

The objective of this project is to develop an IoT system that monitors daily light exposure for plants using luminosity sensors. The system helps determine the optimal placement of plant pots based on each plant's specific light requirements, improving plant growth and vitality.

## Motivation

Proper light exposure is crucial for the health of plants. However, determining the best position for a plant is often a trial-and-error process, leading to suboptimal growth and even plant death. This project aims to address this issue by providing a data-driven approach to optimize plant placement, ensuring they receive the ideal amount of light.

## Specifications

### Hardware
- **ESP32** X ≥ 2 microcontroller.
- **Luminosity Sensors (LDR sensors)**: X ≥ 2 sensors (one in the plant pot, others in potential plant positions).

### Data Acquisition
- Use ESP32 or a similar microcontroller to acquire sensor data periodically.
- Transmit data using **CoAP** protocol.
- Each sensor reading includes a sensor ID and its location.
- The system can receive configuration updates from the Data Proxy via **MQTT** protocol.
  - **Commands to Implement**:
    1. **sampling rate**: Interval between consecutive sensor readings.
    2. **change position**: Move the sensor from one position to another as specified.

### Data Proxy
- A Python application running outside the microcontroller (on a laptop).
- Receives sensor data and sends it to an **InfluxDB** instance.
- Enables configuration updates through MQTT.
- Allows the user to set plant details (type, required light, associated sensor) and define sensor positions (ID, name, description).

### InfluxDB
- A time-series database to store the sensor data.

### Data Analytics Module
- A Python script that processes solar light data for each position.
- Predicts the light exposure for the next N hours.
- Sends predictions to InfluxDB.
- Determines the optimal position for each plant based on light predictions.

### Grafana
- A dashboard to visualize the collected time-series data.
- Displays graphs for each position and plant, showing both predicted and actual light exposure.

### Evaluation
- **Mean Square Error (MSE)**: Evaluate the accuracy of the predicted light exposure.
- **Mean Latency**: Measure the latency in the data acquisition process.

### Bonus Features
- **Front-end Application**:
  - A web application to visualize the layout of a house.
  - Allows users to add, delete, and modify plant and sensor positions.
- **Telegram Bot**:
  - A bot that notifies users when to change plant positions.
  - Users can update plant positions via the bot.

## How to Use

1. **Hardware Setup**: Connect the ESP32 and LDR sensors as per the circuit diagram.
2. **Software Setup**:
   - Clone the repository.
   - Flash the ESP32 with the provided firmware.
   - Set up the Data Proxy and configure InfluxDB.
   - Run the Data Analytics module.
   - Set up the Grafana dashboard using the provided configuration.
3. **Running the System**:
   - Start the Data Proxy to begin receiving sensor data.
   - Monitor the plant positions using Grafana.
   - Optionally, interact with the front-end application or Telegram bot for enhanced control.

## Future Work

- Expand the system to include other environmental factors such as temperature and humidity.
- Integrate with smart home systems for automated plant care.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgements

- [Arduino](https://www.arduino.cc/) for sensor implementation.
- [CoAP](https://aiocoap.readthedocs.io/en/latest/) for sensor data transmission.
- [MQTT](https://pypi.org/project/paho-mqtt/) for sensor settings.
- [InfluxDB](https://www.influxdata.com/) for time-series data management.
- [Grafana](https://grafana.com/) for data visualization.
- [ESP32](https://www.espressif.com/en/products/socs/esp32) for microcontroller support.

---

**Note**: This project is part of an academic assignment and is not intended for commercial use.