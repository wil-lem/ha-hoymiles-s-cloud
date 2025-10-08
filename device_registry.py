# custom_components/hoymiles_cloud/device_registry.py

"""
Centralized device registry helper for consistent device creation across components.
"""

def create_station_device_info(station_id: str, station_name: str = "Unknown") -> dict:
    """
    Create consistent device info for a Hoymiles station.
    
    Args:
        station_id: The station ID from the API
        station_name: The friendly name of the station (defaults to "Unknown")
        
    Returns:
        Dict containing device info with consistent identifiers and naming
    """
    name = f"Hoymiles Station {station_name}"
    identifier = f"hoymiles_station_{station_id}"
    
    return {
        "identifiers": {(identifier,)},
        "name": name,
        "manufacturer": "Hoymiles",
        "model": "X-Series",
    }


def create_module_device_info(module_id: str, station_device_identifier: str) -> dict:
    """
    Create consistent device info for a solar module.
    
    Args:
        module_id: The module ID from the API
        station_device_identifier: The parent station device identifier
        
    Returns:
        Dict containing device info for the module linked to its station
    """
    return {
        "identifiers": {(f"hoymiles_module_{module_id}",)},
        "name": f"Solar Panel {module_id}",
        "manufacturer": "Hoymiles",
        "model": "Solar Module",
        "via_device": (station_device_identifier,),
    }