# Hoymiles Nimbus - S-Cloud Integration for Home Assistant

This is a **proof of concept** custom component for Home Assistant that integrates with the Hoymiles S-Cloud platform. It provides comprehensive monitoring and control capabilities for solar panel installations connected through Hoymiles microinverters.

## About Nimbus
**Nimbus** (Latin for "cloud") represents the cloud-based nature of this integration with Hoymiles S-Cloud services. Just as a nimbus cloud brings life-giving rain, this integration brings vital solar energy data and control capabilities to your Home Assistant setup, creating a seamless bridge between your solar installation and smart home automation.

> **Disclaimer**:  
> This project is not affiliated with Hoymiles or any other company. It is provided as-is for experimental purposes. Use at your own risk.

---

## Nimbus Features

### Station-Level Monitoring
- **Real-time Power Output**: Monitor current power generation from your entire solar installation
- **Daily Energy Production**: Track total energy produced each day in kWh
- **Station Overview**: Get comprehensive station status and performance metrics

### Individual Solar Panel Monitoring
- **Per-Panel Power Tracking**: Monitor power output from each individual solar panel
- **Voltage & Current Sensors**: Track electrical parameters (voltage and current) for each panel
- **Panel Performance Analysis**: Compare performance across different panels to identify issues
- **Position Mapping**: View panel layout with X/Y coordinates for spatial awareness

### Intelligent Power Control
- **Dynamic Power Limiting**: Adjust power output percentage of microinverters (5-100%)
- **Smart Throttling**: Automatic rate limiting prevents API overload while ensuring timely updates
- **Delayed Write Protection**: Prevents rapid successive changes that could stress the system

### Enhanced Device Management
- **Unified Device Registry**: Centralized device creation ensures consistent naming across all components
- **Hierarchical Organization**: Solar panels are properly linked to their parent stations
- **Consistent Identifiers**: All entities use standardized naming conventions for better organization

### Advanced System Coordination
- **Shared Data Coordinator**: Efficient data sharing between multiple sensors reduces API calls
- **Automatic Updates**: Smart caching system updates data every 30 seconds when needed
- **Error Resilience**: Graceful handling of missing or invalid data points

---

## Nimbus Installation Guide

### 1. **Download the Nimbus Component**
1. Clone or download this repository.
2. Copy the `ha-hoymiles-s-cloud` folder into your Home Assistant `custom_components` directory:
   ```
   /config/custom_components/ha-hoymiles-s-cloud/
   ```

### 2. **Restart Home Assistant**
- Restart Home Assistant to load the Nimbus custom component.

### 3. **Add the Nimbus Integration**
1. Go to **Settings > Devices & Services** in the Home Assistant UI.
2. Click **Add Integration** and search for "Hoymiles Nimbus".
3. Enter your Hoymiles S-Cloud credentials and the base URL (default: `https://neapi.hoymiles.com/`).

### 4. **Configure Nimbus Settings**
- After adding the integration, you can configure it further by clicking the **Configure** button in the **Devices & Services** section.

---

## Using Hoymiles Nimbus

### Available Entities
Once installed, Nimbus creates several types of entities for comprehensive monitoring:

#### Station Entities (Per Installation)
- **`sensor.hoymiles_station_[name]_current_power`** - Real-time power output in watts
- **`sensor.hoymiles_station_[name]_daily_energy`** - Daily energy production in kWh  
- **`number.hoymiles_station_[name]_power_level`** - Power limit control (5-100%)

#### Individual Solar Panel Entities (Per Panel)
- **`sensor.hoymiles_station_[name]_panel_[id]_power`** - Per-panel power output in watts
- **`sensor.hoymiles_station_[name]_panel_[id]_voltage`** - Panel voltage in volts
- **`sensor.hoymiles_station_[name]_panel_[id]_current`** - Panel current in amperes

### Device Organization
- All entities are properly grouped under their respective devices in Home Assistant
- Station devices contain the main power/energy sensors and power level controls  
- Individual solar panel devices are linked to their parent station for easy navigation
- Consistent naming ensures all related entities are easily identifiable

---

## Nimbus Limitations
- This is a **proof of concept** and may not handle all edge cases.
- The component relies on the Hoymiles S-Cloud API, which may change or become unavailable without notice.
- API calls are intelligently throttled (30-second intervals) to avoid excessive usage while maintaining responsiveness.
- Power level changes are rate-limited to prevent rapid successive modifications that could impact system stability.

---

## Future Nimbus Enhancements
- **Historical Data Analysis**: Add support for retrieving and analyzing historical performance data
- **Advanced Monitoring**: Implement microinverter health monitoring and diagnostic features  
- **Weather Integration**: Correlate solar performance with weather data for predictive analytics
- **Performance Alerts**: Add automated notifications for underperforming panels or system issues
- **Energy Optimization**: Develop intelligent power management based on usage patterns
- **Multi-Site Support**: Enhanced support for installations across multiple locations
- **Improved Error Handling**: More robust error recovery and user feedback mechanisms
- **Unit Testing Suite**: Comprehensive testing framework for better reliability and maintenance

---

## Disclaimer
This project is not affiliated with Hoymiles or any other company. It is provided as-is for experimental purposes. Use at your own risk. The author is not responsible for any issues that may arise from using this component.

---

## Feedback
If you encounter any issues or have suggestions for improvement, feel free to open an issue or contribute to the project.