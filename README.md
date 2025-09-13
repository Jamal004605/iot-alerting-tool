IoT-Alerting-Tool 🚨

A Python-based tool to monitor values (temperature, pressure, vibration, humidity, etc.) from **MQTT** or **Modbus** sources and send **email alerts** when thresholds are crossed.  

## ✨ Features

- 📡 Supports **MQTT** and **Modbus** protocols  
- 🔔 Sends **email alerts** if values go out of range  
- ⚙️ Configurable through a single YAML file (`config.yml`)  
- 📝 Easy logging of monitored values and alerts  
- 🔒 Keeps sensitive settings outside of code  

## 📂 Project Structure

  iot-alerting-tool/
  │── main.py # Main program
  │── config.example.yml # Example configuration file
  │── requirements.txt # Python dependencies
  │── README.md # Project documentation
  │── .gitignore # Ignore sensitive files
