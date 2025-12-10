"""Config flow for Hoymiles S-Cloud integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .hoymiles_client import HoymilesClient

DOMAIN = "hoymiles_nimbus"


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("username"): str,
    vol.Required("password"): str,
    vol.Optional("base_url", default="https://neapi.hoymiles.com/"): str,
})


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    try:
        client = HoymilesClient(
            username=data["username"],
            password=data["password"],
            base_url=data.get("base_url", "https://neapi.hoymiles.com/"),
        )
        
        # Test the connection
        await hass.async_add_executor_job(client.login)
        
        # Return info that you want to store in the config entry.
        return {"title": "Hoymiles Nimbus"}
    except Exception as ex:
        # You can be more specific about different types of connection errors
        if "401" in str(ex) or "authentication" in str(ex).lower():
            raise InvalidAuth from ex
        else:
            raise CannotConnect from ex


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hoymiles S-Cloud."""
    
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
                # Update the config entry with new data
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=user_input
                )
                return self.async_create_entry(title="", data={})
            except CannotConnect:
                errors = {"base": "cannot_connect"}
            except InvalidAuth:
                errors = {"base": "invalid_auth"}
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors = {"base": "unknown"}
        else:
            errors = {}

        # Pre-fill the form with existing values
        current_data = self.config_entry.data
        options_schema = vol.Schema({
            vol.Required("username", default=current_data.get("username", "")): str,
            vol.Required("password", default=current_data.get("password", "")): str,
            vol.Optional("base_url", default=current_data.get("base_url", "https://neapi.hoymiles.com/")): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )