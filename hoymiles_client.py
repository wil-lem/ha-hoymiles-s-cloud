import requests
import yaml
import logging
import hashlib
from cachetools import TTLCache, cached

_LOGGER = logging.getLogger(__name__)


class HoymilesClient:
    def __init__(self, username, password, base_url):
        
        # Set up logging
        _LOGGER.debug("Initializing HoymilesClient")


        self.username = username
        self.password = password
        self.base_url = base_url

        self.uris = {
            "login": "iam/pub/0/auth/login",
            "user_info": "iam/api/1/user/me",
            "count_station_data": "pvm-data/api/0/station/data/count_station_real_data",
            "find": "pvm/api/0/station/find",
        }
        
        self.token = None
        self.cache = TTLCache(maxsize=100, ttl=300)


    def _post_request(self, uri, payload=None, headers=None, use_auth=True, binary=False):
        """Helper method to make POST requests."""
        url = f"{self.base_url}{uri}"
        if headers is None:
            headers = {"Content-Type": "application/json"}
        if use_auth:
            if self.token:
                headers["Authorization"] = self.token
            else:
                raise Exception("Token is not set. Please authenticate first.")

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
                response_data = response.json()
                logging.debug(f"Response JSON: {response_data}")
                return response_data
            except ValueError:
                logging.error("Failed to parse response as JSON")
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
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

        _LOGGER.debug(f"PUT Request URL: {url}")
        _LOGGER.debug(f"PUT Request Payload: {payload}")
        _LOGGER.debug(f"PUT Request Headers: {headers}")

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Attempt to parse the response as JSON
        try:
            response_data = response.json()
            _LOGGER.debug(f"Response JSON: {response_data}")
            return response_data
        except ValueError:
            _LOGGER.error("Failed to parse response as JSON")
            return None

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
      _LOGGER.debug("Logging into Hoymiles S-Cloud...")
      response_data = self.get_token(username=self.username, password=self.get_password_hash())
      if response_data and "data" in response_data and "token" in response_data["data"]:
          self.token = response_data["data"]["token"]
          return True
      else:
          raise Exception("Login failed: Token not found in response")
      
    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def get_user_info(self):
        """Retrieve user information from Hoymiles S-Cloud."""
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

    def put_command(self,action, dev_sn, dev_type, dtu_sn):
        uri = 'pvm-ctl/api/0/dev/command/put'
        {
            "action": action,
            "dev_sn": dev_sn,
            "dev_type": dev_type,
            "dtu_sn": dtu_sn
        }
    
    def turn_off_microinverter(self, dev_sn, dev_type, dtu_sn):
        """Turn off the microinverter."""
        self.put_command(7, dev_sn, 3, dtu_sn)
    
    
    @cached(cache=TTLCache(maxsize=100, ttl=300))
    def findStation(self, sid):
        """Find a station by its ID."""
        payload = {
            "id": sid,
        }
        response = self._post_request(self.uris['find'], payload=payload)

        return response.get('data', {})
    
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
    