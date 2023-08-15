# HA Solcast PV Solar Forecast Integration

Home Assistant(https://www.home-assistant.io) Integration Component

This custom component integrates the Solcast Hobby PV Forecast API into Home Assistant.
[<img src="https://user-images.githubusercontent.com/1471841/135556872-ff5b51ac-699e-4ea5-869c-f9b0d0c5b815.png" width="200">](https://user-images.githubusercontent.com/1471841/135556872-ff5b51ac-699e-4ea5-869c-f9b0d0c5b815.png)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

```
⚠️ Solcast have altered their API limits for new account creators

Solcast now only offer new account creators 10 api calls per day (used to be 50). 
Old account users still have 50 api calls

The integration allows users to disable the auto api polling to create their own automations
to call the update solcast service to poll for new data to allow for the max 10 api poll limit.
```

## Solcast Requirements:
Sign up for an API key (https://solcast.com/)

> Solcast may take up to 24hrs to create the account

Copy the API Key for use with this integration (See [Configuration](#Configuration) below).

## Installation

### HACS *(recommended)*

Easy install by default on HACS. More info [here](https://hacs.xyz/).

<!--
or click on:
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=oziee&repository=ha-solcast-solar&category=plugin)
-->


<details>
<summary><h3>Manually</summary></h3>

You probably **do not** want to do this! Use the HACS method above unless you know what you are doing and have a good reason as to why you are installing manually

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`)
1. If you do not have a `custom_components` directory there, you need to create it
1. In the `custom_components` directory create a new folder called `solcast_solar`
1. Download _all_ the files from the `custom_components/solcast_solar/` directory in this repository
1. Place the files you downloaded in the new directory you created
1. *Restart HA to load the new integration*
1. See [Configuration](#configuration) below

</details>

## Configuration

1. [Click Here](https://my.home-assistant.io/redirect/config_flow_start/?domain=solcast_solar) to directly add a `Solcast Solar` integration **or**<br/>
 a. In Home Assistant, go to Settings -> [Integrations](https://my.home-assistant.io/redirect/integrations/)<br/>
 b. Click `+ Add Integrations` and select `Solcast PV Forecast`<br/>
1. Enter you `Solcast API Key`
1. Click `Submit`

* Create your own [automation](#services) to call the service `solcast_solar.update_forecasts` when you like it to call

* Options can be changed for existing `Solcast PV Forecast` integration in Home Assistant Integrations by selecting `Configure` (cog wheel)

* If you have more than one Solcast account because you have more than 2 rooftop setups, enter both account API keys separated by a comma `xxxxxxxx-xxxxx-xxxx,yyyyyyyy-yyyyy-yyyy` (this does go against Solcast T&C's having more than one account)

* This is your `API Key` not your rooftop id created in Solcast. You can find your API key here [api key](https://toolkit.solcast.com.au/account)

[<img src="https://github.com/oziee/ha-solcast-solar/blob/v3/.github/SCREENSHOTS/install.png" width="200">](https://github.com/oziee/ha-solcast-solar/blob/v3/.github/SCREENSHOTS/install.png)

## Services
There are 2 services for this integration that you can use in automations ([Configuration](#configuration))

| Service | Action |
| --- | --- |
| `solcast_solar.update_forecasts` | Updates the future forecast data only |
| `solcast_solar.clear_all_solcast_data` | Deletes the `solcast.json` cached file |

### Basic HA Automation to manual poll Solcast API data
Create a new HA automation and setup your preferred triggers to manually poll for new data
This is an example.. create your own to your own needs


```yaml
alias: Solcast_update
description: New API call Solcast
trigger:
 - platform: time_pattern
   hours: /4
condition:
 - condition: sun
   before: sunset
   after: sunrise
action:
 - service: solcast_solar.update_forecasts
   data: {}
mode: single
```

or

```yaml
alias: Solcast update
description: ""
trigger:
  - platform: time
    at: "4:00:00"
  - platform: time
    at: "10:00:00"
  - platform: time
    at: "16:00:00"
condition: []
action:
  - service: solcast_solar.update_forecasts
    data: {}
mode: single
```


<details>
<summary><h3>Set up HA Energy Dashboard settings</summary></h3>

Go to the `HA>Settings>Dashboards>Energy`
Click the edit the Solar Production item you have created. 


> **Note**
> _If you do not have a solar sensor in your system then this integration will not work. The graph, and adding the forecast integration rely on there being a sensor setup to be added here_

[<img src="https://user-images.githubusercontent.com/1471841/149643349-d776f1ad-530c-46aa-91dc-8b9e7c7f3123.png" width="200">](https://user-images.githubusercontent.com/1471841/149643349-d776f1ad-530c-46aa-91dc-8b9e7c7f3123.png)


Click the Forecast option button and select the Solcast Solar option.. Click SAVE.. HA will do all the rest for you

[<img src="https://user-images.githubusercontent.com/1471841/174471543-0833b141-0c97-4b90-a058-cf986e89bbce.png" width="200">](https://user-images.githubusercontent.com/1471841/174471543-0833b141-0c97-4b90-a058-cf986e89bbce.png)

</details>

## HA Views:
<details>
<summary><h3>HA Energy Tab</summary></h3>

[<img src="https://user-images.githubusercontent.com/1471841/135556872-ff5b51ac-699e-4ea5-869c-f9b0d0c5b815.png" width="200">](https://user-images.githubusercontent.com/1471841/135556872-ff5b51ac-699e-4ea5-869c-f9b0d0c5b815.png)

</details>
<details>
<summary><h3>Sensors</summary></h3>

| Name | Type | Attributes | Default | Description |
| ------------------------------ | ----------- | ----------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | 
| `Today` | number | Y | `kWh` | Total forecast solar production for today |
| `Tomorrow` | number | Y | `kWh` | Total forecast solar production for day + 1 (tomorrow) |
| `D3` | number | Y | `kWh` | Total forecast solar production for day + 2 (day 3) |
| `D4` | number | Y | `kWh` | Total forecast solar production for day + 3 (day 4) |
| `D5` | number | Y | `kWh` | Total forecast solar production for day + 4 (day 5) |
| `D6` | number | Y | `kWh`| Total forecast solar production for day + 5 (day 6) |
| `D7` | number | Y | `kWh` | Total forecast solar production for day + 6 (day 7) |
| `This Hour` | number | N | `Wh` | Forecasted solar production current hour |
| `Next Hour` | number | N | `Wh` | Forecasted solar production next hour |
| `Remaining Today` | number | N | `kWh` | Predicted remaining solar production today |
| `Peak Forecast Today` | number | N | `Wh` | Highest predicted production within an hour period today |
| `Peak Time Today` | date/time | N |  | Hour of max forecasted production of solar today |
| `Peak Forecast Tomorrow` | number | N | `Wh` | Highest predicted production within an hour period tomorrow |
| `Peak Time Tomorrow` | date/time | N |  | Hour of max forecasted production of solar tomorrow |

### Configuration

| Name | Type | Attributes | Default | Description |
| ------------------------------ | ----------- | ----------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | 
| `Rooftop name` | number | Y | `kWh` | Total forecast for rooftop today (attributes contain the solcast rooftop setup) |

### Diagnostic

| Name | Type | Attributes | Default | Description |
| ------------------------------ | ----------- | ----------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | 
| `API Last Polled` | date/time | N |  | Date/time when the API data was polled |
| `API Limit` | number | N | `integer` | Total times the API can been called in a 24 hour period |
| `API used` | number | N | `integer` | Total times the API has been called today (API counter resets to zero at midnight UTC) |


</details>

<summary><h3>Credits</summary></h3>

Modified from the great works of
* dannerph/homeassistant-solcast
* cjtapper/solcast-py
* home-assistant-libs/forecast_solar
