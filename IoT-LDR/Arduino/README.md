# Arduino
The current folder contains the Arduino code to be flashed in the sensor nodes.

## Specifications

### Hardware
- **ESP32C6**
- **LDR sensors**
- **$100n$F capacitor**
- **$10k\Omega$ resistor**

### Data acquisition
- The ESP32 acquires the LDR data periodically.
- The sampling period and position is chosen by the user and can be set anytime through the provided CLI, the configuration are sent through the **MQTT** protocol.
- Wi-Fi connection is required to send the data, make sure to set the proper name and password for your use case.
- Transmission of the data is performed using **CoAP** protocol, make sure to set the proper IP address and port for your use case.
- If CoAP transmission fails, the sensed data is sent direcly to InfluxDB database.
