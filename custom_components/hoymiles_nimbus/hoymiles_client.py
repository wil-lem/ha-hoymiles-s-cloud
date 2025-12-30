import datetime
import requests
import yaml
import logging
import hashlib
from cachetools import TTLCache, cached

# Handle imports for both standalone and Home Assistant contexts
try:
    from .classes.micro_inverter import Microinverter
    from .classes.solar_module import SolarModule
    from .classes.station import Station
    from .parsers import ProtobufParser
except ImportError:
    from classes.micro_inverter import Microinverter
    from classes.solar_module import SolarModule
    from classes.station import Station
    from parsers import ProtobufParser

_LOGGER = logging.getLogger(__name__)


class HoymilesClient:
    """
    Client for interacting with Hoymiles S-Cloud API.
    
    This class provides methods organized into different categories:
    - Authentication: login, token management
    - HTTP helpers: internal request methods
    - Data fetching: retrieve information from API
    - Control operations: send commands to devices
    - System mapping: build system hierarchy
    - Utilities: helper functions
    """
    
    def __init__(self, username, password, base_url):
        """Initialize the Hoymiles client with credentials and base URL."""
        _LOGGER.debug("Initializing HoymilesClient")
        
        self.username = username
        self.password = password
        self.base_url = base_url
        
        # API endpoint URIs
        self.uris = {
            "login": "iam/pub/0/auth/login",
            "user_info": "iam/api/1/user/me",
            "count_station_data": "pvm-data/api/0/station/data/count_station_real_data",
            "find": "pvm/api/0/station/find",
            "select_by_station": "pvm/api/0/dev/micro/select_by_station",
            "micro_find": "pvm/api/0/dev/micro/find",
            "module_details": "pvm-data/api/0/module/data/find_details",
            "select_all_arrays": "pvm/api/0/dev/array_v3/select_all",
            "down_module_day_data": "pvm-data/api/0/module/data/down_module_day_data",
            "down_station_day_data": "pvm-data/api/0/station/down_station_day_data",
        }
        
        self.token = None
        self.cache = TTLCache(maxsize=100, ttl=300)

    # ============================================================================
    # HTTP HELPER METHODS
    # ============================================================================


    def _post_request(self, uri, payload=None, headers=None, use_auth=True, binary=False, response_type='json'):
        """Helper method to make POST requests."""
        url = f"{self.base_url}{uri}"
        if headers is None:
            headers = {"Content-Type": "application/json"}
        if use_auth:
            if self.token:
                headers["Authorization"] = self.token
            else:
                raise Exception("Token is not set. Please authenticate first.")

        _LOGGER.warning("API Request: POST %s with params: %s", url, payload)
        _LOGGER.debug(f"POST Request URL: {url}")
        _LOGGER.debug(f"POST Request Payload: {payload}")
        _LOGGER.debug(f"POST Request Headers: {headers}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        try:
            _LOGGER.debug(f"Response Status Code: {response.status_code}")
            _LOGGER.debug(f"Response Headers: {response.headers}")
            response.raise_for_status()
            
            # Attempt to parse the response as JSON
            try:
                if response_type == 'protobuf' and binary:
                    parser = ProtobufParser(response.content)
                    _LOGGER.debug("API Response: %s - Protobuf data received", response.status_code)
                    return parser
                response_data = response.json()
                logging.debug(f"Response JSON: {response_data}")
                _LOGGER.debug("API Response: %s - Success", response.status_code)
                return response_data
            except ValueError:
                logging.error("Failed to parse response as JSON")
                _LOGGER.debug("API Response: %s - Failed to parse JSON", response.status_code)
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            _LOGGER.warning("API Response: Request failed - %s", str(e))
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            _LOGGER.warning("API Response: Unexpected error - %s", str(e))
            raise
        
    def _put_request(self, uri, payload=None, headers=None):
        """Helper method to make PUT requests."""
        url = f"{self.base_url}{uri}"
        if headers is None:
            headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = self.token
        else:
            raise Exception("Token is not set. Please authenticate first.")

        _LOGGER.warning("API Request: PUT %s with params: %s", url, payload)
        _LOGGER.debug(f"PUT Request URL: {url}")
        _LOGGER.debug(f"PUT Request Payload: {payload}")
        _LOGGER.debug(f"PUT Request Headers: {headers}")

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Attempt to parse the response as JSON
        try:
            response_data = response.json()
            _LOGGER.debug(f"Response JSON: {response_data}")
            _LOGGER.debug("API Response: %s - Success", response.status_code)
            return response_data
        except ValueError:
            _LOGGER.error("Failed to parse response as JSON")
            _LOGGER.debug("API Response: %s - Failed to parse JSON", response.status_code)
            return None

    # ============================================================================
    # AUTHENTICATION METHODS
    # ============================================================================

    def get_password_hash(self):
      password = self.password.encode('utf-8')
      passwordHash = hashlib.md5(password)
      return passwordHash.hexdigest()

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def get_token(self,username, password):
      payload = {
          "user_name": username,
          "password": password,
      }
      _LOGGER.debug(f"Payload for get_token: {payload}")
      return self._post_request(self.uris['login'], payload=payload, use_auth=False)
    

    def login(self):
      """Authenticate with Hoymiles S-Cloud and retrieve a token."""
      _LOGGER.warning("Logging into Hoymiles S-Cloud for user: %s", self.username)
      response_data = self.get_token(username=self.username, password=self.get_password_hash())
      if response_data and "data" in response_data and "token" in response_data["data"]:
          self.token = response_data["data"]["token"]
          _LOGGER.warning("Successfully authenticated with Hoymiles S-Cloud")
          return True
      else:
          _LOGGER.error("Login failed: Token not found in response")
          raise Exception("Login failed: Token not found in response")

    # ============================================================================
    # DATA FETCHING METHODS
    # ============================================================================

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def select_by_station(self, station_id):
        """Select microinverters by station ID."""
        payload = {
            "sid": station_id,
            "page": 1,
            "page_size": 1000,
            "show_warn": 0
        }
        response = self._post_request(self.uris['select_by_station'], payload=payload)

        return response.get("data", {})
    
    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def micro_find(self, micro_id, station_id):
        """Find a microinverter by its ID."""
        payload = {
            "id": micro_id,
            "sid": station_id,
        }
        response = self._post_request(self.uris['micro_find'], payload=payload)
        return response.get('data', {})

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def module_details(self, station_id, micro_id, micro_sn, port, time):
        """Retrieve module details by its ID."""
        payload = {
            "sid": station_id,
            "mi_id": micro_id,
            "mi_sn": micro_sn,
            "port": port,
            "time": time,
            "warn_code": 1,
        }

        response = self._post_request(self.uris['module_details'], payload=payload)
        return response.get('data', {})

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def get_user_info(self):
        """Retrieve user information from Hoymiles S-Cloud. [UNUSED]"""
        return self._post_request(self.uris['user_info'])

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def select_by_page(self, type):
        uri_map = {
            "station":  "pvm/api/0/station/select_by_page",
            "dtu":      "pvm/api/0/dev/dtu/select_by_page",
            "micro":    "pvm/api/0/dev/micro/select_by_page",
            # Add more types here if needed
        }

        # Get the URI based on the type
        uri = uri_map.get(type)
        if not uri:
            raise ValueError(f"Invalid type for select_by_page: {type}")

        payload = {
            "page": 1,
            "page_size": 100,
        }
        response = self._post_request(uri, payload=payload)

        return response.get("data", {}).get("list", [])

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def count_station_real_data(self,id):
        """Get the count of station real data."""
        _LOGGER.debug(f"Getting count of station real data for ID: {id}")
        payload = {
            "sid": id,
        }
        return self._post_request(self.uris['count_station_data'], payload=payload)

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def findStation(self, sid):
        """Find a station by its ID."""
        payload = {
            "id": sid,
        }
        response = self._post_request(self.uris['find'], payload=payload)
        return response.get('data', {})

    def down_module_day_data(self, sid, date):
        """Download module day data for a specific date."""
        payload = {
            "sid": sid,
            "date": date,
        }
        response = self._post_request(self.uris['down_module_day_data'], payload=payload, response_type='protobuf', binary=True)
        return response

    # ============================================================================
    # CONTROL OPERATIONS
    # ============================================================================

    
    def turn_off_microinverter(self, dev_sn, dev_type, dtu_sn):
        """Turn off the microinverter. [UNUSED]"""
        self.put_command(7, dev_sn, 3, dtu_sn)

    def set_power_limit(self, sid, power_limit):
        """Set the power limit for a microinverter."""
        power_limit = min(100, int(power_limit))
        power_limit = max(5, int(power_limit))
        payload = {
            "action": 8,
            "data": {
                "sid": sid,
                "power_limit": power_limit,
                "enable": 1
            }
        }

        _LOGGER.debug(f"Setting power limit for SID {sid} to {power_limit}%")
        
        uri = 'pvm-ctl/api/0/dev/command/put'
        return self._put_request(uri, payload=payload)

    # ============================================================================
    # SYSTEM MAPPING AND DATA PROCESSING
    # ============================================================================
    
    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def map_system(self):
        """Build a hierarchical system map of stations, microinverters, and modules."""
        stations = self.select_by_page("station")
        system = []
        if not stations:
            _LOGGER.warning("No stations found.")
            return system
        
        for station_data in stations:
            station = Station(station_data.get("id"), station_data.get("name"))
            
            # Fetch microinverters for the station
            microinverters = self.select_by_station(station.station_id)
            if not microinverters:
                _LOGGER.warning(f"No microinverters found for station ID {station.station_id}.")
                continue
                
            for micro_data in microinverters.get("list", []):
                micro_id = micro_data.get("id")
                sn = micro_data.get("sn")
                microinverter = Microinverter(micro_id, sn)
                station.add_microinverter(microinverter)
                
                # Fetch module details for each port
                micro_details = self.micro_find(micro_id, station.station_id)
                for port_info in micro_details.get("layout_list", []):
                    module_id = f"{sn}-{port_info.get('port')}"
                    port = port_info.get("port")
                    x = port_info.get("x")
                    y = port_info.get("y")
                    solar_module = SolarModule(module_id, port, x, y)
                    microinverter.add_module(solar_module)
                    
            system.append(station)
        return system
    
    
    def fill_system_data(self, system, date=None):
        """Fill system hierarchy with actual performance data for a given date."""
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        _LOGGER.debug(f"Filling system data for date: {date}")
        for station in system:
            sid = station.station_id
            data = self.down_module_day_data(sid, date)
            station.set_data(data)
