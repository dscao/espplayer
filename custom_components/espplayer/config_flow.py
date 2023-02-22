from __future__ import annotations
import logging
import requests
import json

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback, HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.const import  CONF_NAME, CONF_SCAN_INTERVAL


from .const import CONF_SENSORSTATE, CONF_ESPPLAY, CONF_ESPSTOP, CONF_ESPVOL, CONF_ESPWAN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for EsphomePlayer component."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            self.config = user_input
            await self.async_set_unique_id(
                f"espplayer-{self.config[CONF_ESPPLAY]}"
            )
            self._abort_if_unique_id_configured()
            
            test = self.get_entitystate(self.config[CONF_SENSORSTATE])
            _LOGGER.debug("test: %s", test)
            if test == None  or test == "unavailable":
                errors["base"] = "nosensorstate"
              
            
            if not errors:
                return self.async_create_entry(title=self.config[CONF_NAME], data=self.config)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME, default="esp_wav_player"): str,
                        vol.Required(CONF_SENSORSTATE, default="media_player.rf_media_player"): str,
                        vol.Required(CONF_ESPPLAY, default="esphome.rf_bridge_play_audio"): str,
                        vol.Required(CONF_ESPSTOP, default="esphome.rf_bridge_stop_audio"): str,
                    }
            ),
            errors=errors,
        )
        
    def get_entitystate(self,entityid):
        currentState=None
        entity = self.hass.states.get(entityid)
        if entity is None:
            _LOGGER.warning("Unable to find entity %s", entityid)
            self.entityFound = False
        else:
            self.entityFound = True
            currentState = entity.state
        return currentState
        
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a ESPPLAYER options flow.

    Configures the single instance and updates the existing config entry.
    """

    def __init__(self, config_entry):
        """Initialize autoamap options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ESPVOL,
                        default=self.config_entry.options.get(CONF_ESPVOL, "None"),
                    ): vol.All(vol.Coerce(str)),
                    vol.Optional(
                        CONF_ESPWAN,
                        default=self.config_entry.options.get(CONF_ESPWAN, "auto"),
                    ): vol.All(vol.Coerce(str))
                }
            ),
        )
