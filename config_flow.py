import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .hoymiles_client import HoymilesClient  # Import the client class


DOMAIN = "hoymiles_cloud"

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required("username"): str,
    vol.Required("password"): str,
    vol.Optional("base_url", default="https://neapi.hoymiles.com/"): str,
})

class HoymilesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Validate the credentials using HoymilesClient
            try:
                client = HoymilesClient(
                    username=user_input["username"],
                    password=user_input["password"],
                    base_url=user_input.get("base_url", "https://neapi.hoymiles.com/"),
                )
                # Attempt to log in
                await self.hass.async_add_executor_job(client.login)
                # If successful, create the entry
                return self.async_create_entry(title="Hoymils S-Cloud", data=user_input)
            except Exception as e:
                _LOGGER.error(f"Login failed: {e}")
                errors["base"] = "invalid_credentials"


        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HoymilesOptionsFlowHandler(config_entry)

class HoymilesOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            try:
                client = HoymilesClient(
                    username=user_input["username"],
                    password=user_input["password"],
                    base_url=user_input.get("base_url", "https://neapi.hoymiles.com/"),
                )
                # Attempt to log in
                await self.hass.async_add_executor_job(client.login)   
            
                # Save the updated options
                self.hass.config_entries.async_update_entry(self.config_entry, data=user_input)
                
                # Return a FlowResult indicating the options were successfully updated
                return self.async_create_entry(title="", data={})
            except Exception as e:
                _LOGGER.error(f"Login failed: {e}")
                return self.async_show_form(
                    step_id="init",
                    data_schema=vol.Schema({
                        vol.Required("username", default=user_input["username"]): str,
                        vol.Required("password", default=user_input["password"]): str,
                        vol.Optional("base_url", default=user_input.get("base_url", "https://neapi.hoymiles.com/")): str,
                    }),
                    errors={"base": "invalid_credentials"},
                )
        
        # Pre-fill the form with existing values
        current_data = self.config_entry.data
        data_schema = vol.Schema({
            vol.Required("username", default=current_data.get("username", "")): str,
            vol.Required("password", default=current_data.get("password", "")): str,
            vol.Optional("base_url", default=current_data.get("base_url", "https://neapi.hoymiles.com/")): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )