# Hoymiles S-Cloud Custom Component (Proof of Concept)

This is a **proof of concept** custom component for Home Assistant that integrates with the Hoymiles S-Cloud platform. It allows users to monitor and control the power output of their solar panel installations connected through Hoymiles microinverters.

> **Disclaimer**:  
> This project is not affiliated with Hoymiles or any other company. It is provided as-is for experimental purposes. Use at your own risk.

---

## Features
- **Monitor Power Output**: View the current power output of your solar panel installation.
- **Control Power Levels**: Adjust the power output of your Hoymiles microinverters directly from Home Assistant.
- **Throttled Updates**: Minimize API calls to avoid overloading the Hoymiles S-Cloud platform.
- **Configurable Options**: Update credentials and base URL through the Home Assistant UI.

---

## Installation Instructions

### 1. **Download the Component**
1. Clone or download this repository.
2. Copy the `hoymiles_cloud` folder into your Home Assistant `custom_components` directory:
   ```
   /config/custom_components/hoymiles_cloud/
   ```

### 2. **Restart Home Assistant**
- Restart Home Assistant to load the custom component.

### 3. **Add the Integration**
1. Go to **Settings > Devices & Services** in the Home Assistant UI.
2. Click **Add Integration** and search for "Hoymiles S-Cloud".
3. Enter your Hoymiles S-Cloud credentials and the base URL (default: `https://neapi.hoymiles.com/`).

### 4. **Configure the Integration**
- After adding the integration, you can configure it further by clicking the **Configure** button in the **Devices & Services** section.

---

## Usage
- **Sensors**: View the current power output and energy data from your solar panel installation.
- **Number Entities**: Adjust the power output percentage of your Hoymiles microinverters.

---

## Known Limitations
- This is a **proof of concept** and may not handle all edge cases.
- The component relies on the Hoymiles S-Cloud API, which may change or become unavailable without notice.
- API calls are throttled to avoid excessive usage, which may result in delayed updates.

---

## Future Improvements
- Add support for more Hoymiles S-Cloud features.
- Improve error handling and logging.
- Optimize API usage further.
- Add unit tests for better reliability.

---

## Disclaimer
This project is not affiliated with Hoymiles or any other company. It is provided as-is for experimental purposes. Use at your own risk. The author is not responsible for any issues that may arise from using this component.

---

## Feedback
If you encounter any issues or have suggestions for improvement, feel free to open an issue or contribute to the project.