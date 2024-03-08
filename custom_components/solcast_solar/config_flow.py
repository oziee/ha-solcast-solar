"""Config flow for Solcast Solar integration."""

from __future__ import annotations
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from homeassistant import config_entries
from .const import DOMAIN, CONFIG_OPTIONS, CUSTOM_HOUR_SENSOR


@config_entries.HANDLERS.register(DOMAIN)
class SolcastSolarFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solcast Solar."""

    VERSION = 6  # v5 started in 4.0.8, #6 started 4.0.15

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> SolcastSolarOptionFlowHandler:
        """Get the options flow for this handler."""
        return SolcastSolarOptionFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title="Solcast Solar",
                data={},
                options={
                    CONF_API_KEY: user_input[CONF_API_KEY],
                    "damp00": 1.0,
                    "damp01": 1.0,
                    "damp02": 1.0,
                    "damp03": 1.0,
                    "damp04": 1.0,
                    "damp05": 1.0,
                    "damp06": 1.0,
                    "damp07": 1.0,
                    "damp08": 1.0,
                    "damp09": 1.0,
                    "damp10": 1.0,
                    "damp11": 1.0,
                    "damp12": 1.0,
                    "damp13": 1.0,
                    "damp14": 1.0,
                    "damp15": 1.0,
                    "damp16": 1.0,
                    "damp17": 1.0,
                    "damp18": 1.0,
                    "damp19": 1.0,
                    "damp20": 1.0,
                    "damp21": 1.0,
                    "damp22": 1.0,
                    "damp23": 1.0,
                    "customhoursensor": 1,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY, default=""): str,
                }
            ),
        )


class SolcastSolarOptionFlowHandler(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            if "solcast_config_action" in user_input:
                nextAction = user_input["solcast_config_action"]
                if nextAction == "configure_dampening":
                    return await self.async_step_dampen()
                elif nextAction == "configure_api":
                    return await self.async_step_api()
                elif nextAction == "configure_customsensor":
                    return await self.async_step_customsensor()
                else:
                    errors["base"] = "incorrect_options_action"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("solcast_config_action"): SelectSelector(
                        SelectSelectorConfig(
                            options=CONFIG_OPTIONS,
                            mode=SelectSelectorMode.LIST,
                            translation_key="solcast_config_action",
                        )
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_api(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            allConfigData = {**self.config_entry.options}
            k = user_input["api_key"].replace(" ", "").strip()
            k = ",".join([s for s in k.split(",") if s])
            allConfigData["api_key"] = k

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                title="Solcast Solar",
                options=allConfigData,
            )
            return self.async_create_entry(title="Solcast Solar", data=None)

        return self.async_show_form(
            step_id="api",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_API_KEY,
                        default=self.config_entry.options.get(CONF_API_KEY),
                    ): str,
                }
            ),
        )

    async def async_step_dampen(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:  # user_input=None):
        """Manage the hourly factor options."""

        errors = {}

        damp00 = self.config_entry.options["damp00"]
        damp01 = self.config_entry.options["damp01"]
        damp02 = self.config_entry.options["damp02"]
        damp03 = self.config_entry.options["damp03"]
        damp04 = self.config_entry.options["damp04"]
        damp05 = self.config_entry.options["damp05"]
        damp06 = self.config_entry.options["damp06"]
        damp07 = self.config_entry.options["damp07"]
        damp08 = self.config_entry.options["damp08"]
        damp09 = self.config_entry.options["damp09"]
        damp10 = self.config_entry.options["damp10"]
        damp11 = self.config_entry.options["damp11"]
        damp12 = self.config_entry.options["damp12"]
        damp13 = self.config_entry.options["damp13"]
        damp14 = self.config_entry.options["damp14"]
        damp15 = self.config_entry.options["damp15"]
        damp16 = self.config_entry.options["damp16"]
        damp17 = self.config_entry.options["damp17"]
        damp18 = self.config_entry.options["damp18"]
        damp19 = self.config_entry.options["damp19"]
        damp20 = self.config_entry.options["damp20"]
        damp21 = self.config_entry.options["damp21"]
        damp22 = self.config_entry.options["damp22"]
        damp23 = self.config_entry.options["damp23"]

        if user_input is not None:
            try:
                damp00 = user_input["damp00"]
                damp01 = user_input["damp01"]
                damp02 = user_input["damp02"]
                damp03 = user_input["damp03"]
                damp04 = user_input["damp04"]
                damp05 = user_input["damp05"]
                damp06 = user_input["damp06"]
                damp07 = user_input["damp07"]
                damp08 = user_input["damp08"]
                damp09 = user_input["damp09"]
                damp10 = user_input["damp10"]
                damp11 = user_input["damp11"]
                damp12 = user_input["damp12"]
                damp13 = user_input["damp13"]
                damp14 = user_input["damp14"]
                damp15 = user_input["damp15"]
                damp16 = user_input["damp16"]
                damp17 = user_input["damp17"]
                damp18 = user_input["damp18"]
                damp19 = user_input["damp19"]
                damp20 = user_input["damp20"]
                damp21 = user_input["damp21"]
                damp22 = user_input["damp22"]
                damp23 = user_input["damp23"]

                allConfigData = {**self.config_entry.options}
                allConfigData["damp00"] = damp00
                allConfigData["damp01"] = damp01
                allConfigData["damp02"] = damp02
                allConfigData["damp03"] = damp03
                allConfigData["damp04"] = damp04
                allConfigData["damp05"] = damp05
                allConfigData["damp06"] = damp06
                allConfigData["damp07"] = damp07
                allConfigData["damp08"] = damp08
                allConfigData["damp09"] = damp09
                allConfigData["damp10"] = damp10
                allConfigData["damp11"] = damp11
                allConfigData["damp12"] = damp12
                allConfigData["damp13"] = damp13
                allConfigData["damp14"] = damp14
                allConfigData["damp15"] = damp15
                allConfigData["damp16"] = damp16
                allConfigData["damp17"] = damp17
                allConfigData["damp18"] = damp18
                allConfigData["damp19"] = damp19
                allConfigData["damp20"] = damp20
                allConfigData["damp21"] = damp21
                allConfigData["damp22"] = damp22
                allConfigData["damp23"] = damp23

                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title="Solcast Solar",
                    options=allConfigData,
                )

                return self.async_create_entry(title="Solcast Solar", data=None)
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="dampen",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "damp00", description={"suggested_value": damp00}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp01", description={"suggested_value": damp01}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp02", description={"suggested_value": damp02}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp03", description={"suggested_value": damp03}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp04", description={"suggested_value": damp04}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp05", description={"suggested_value": damp05}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp06", description={"suggested_value": damp06}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp07", description={"suggested_value": damp07}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp08", description={"suggested_value": damp08}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp09", description={"suggested_value": damp09}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp10", description={"suggested_value": damp10}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp11", description={"suggested_value": damp11}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp12", description={"suggested_value": damp12}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp13", description={"suggested_value": damp13}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp14", description={"suggested_value": damp14}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp15", description={"suggested_value": damp15}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp16", description={"suggested_value": damp16}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp17", description={"suggested_value": damp17}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp18", description={"suggested_value": damp18}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp19", description={"suggested_value": damp19}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp20", description={"suggested_value": damp20}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp21", description={"suggested_value": damp21}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp22", description={"suggested_value": damp22}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                    vol.Required(
                        "damp23", description={"suggested_value": damp23}
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
                }
            ),
            errors=errors,
        )

    async def async_step_customsensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the custom x hour sensor option."""

        errors = {}

        customhoursensor = self.config_entry.options[CUSTOM_HOUR_SENSOR]

        if user_input is not None:
            try:
                customhoursensor = user_input[CUSTOM_HOUR_SENSOR]

                allConfigData = {**self.config_entry.options}
                allConfigData[CUSTOM_HOUR_SENSOR] = customhoursensor

                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title="Solcast Solar",
                    options=allConfigData,
                )

                return self.async_create_entry(title="Solcast Solar", data=None)
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="customsensor",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CUSTOM_HOUR_SENSOR,
                        description={"suggested_value": customhoursensor},
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=144)),
                }
            ),
            errors=errors,
        )
