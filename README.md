# Solcast Solar 

Home Assistant(https://www.home-assistant.io/) Component

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

This custom component integrates the Solcast API into Home Assistant.

Modified from the great works of
* dannerph/homeassistant-solcast
* cjtapper/solcast-py
* home-assistant-libs/forecast_solar
## Basic Installation/Configuration Instructions:
Add a new HA Integration selecting 'Solcast PV Solar'. 

If the integration is not listed in HACS, click on the three dots at the top right and select custom repositories. Enter `https://github.com/oziee/ha-solcast-solar` and pick Integration as category.

Once downloaded, you can add the integration using Configuration | Devices & Services | Add Integration.

Setup the Recorder to record data.. something like
```
recorder:
  purge_keep_days: 31
  include:
    entity_globs:
      - sensor.solcast*
```

<img width="301" alt="Screen Shot 2022-02-03 at 12 46 02 pm" src="https://user-images.githubusercontent.com/1471841/152277906-b01cf56d-36e6-4176-849b-388125edb7b2.png">

ONLY SET THE OFFSET to anything other than zero ONLY if your energy graph does not display properly.
Leave it as zero for default and then only if there is a problem change it. [see issue 21](https://github.com/oziee/ha-solcast-solar/issues/21)


If you have more than one Solcast rooftop site, repeat the above sets for each site
(2 sites).. to edit them.. click the item to edit then the configure button will appear

![img6](https://user-images.githubusercontent.com/1471841/149643389-dac7a6bd-71b3-4d57-9b84-262cd728285b.png)

### HA Energy Tab
Go to the HA>Configuration>Energy settings page
Click the edit for the solar production item you have created. 

![img4](https://user-images.githubusercontent.com/1471841/149643349-d776f1ad-530c-46aa-91dc-8b9e7c7f3123.png)

Click the Forecast option button and select all the sites you have.. Click SAVE.. HA will do all the rest for you

![img5](https://user-images.githubusercontent.com/1471841/149643348-cee444cf-d7ac-4304-ae72-d429eccc7b35.png)

#### Getting a Solcast API Key:
Sign up for an API key (https://solcast.com/)

Solcast may take up to 24hrs to apply the 50 API counter from the default 10.. give it time to work:)

Create a Rooftop entity on the Solcast website. This will generate a rooftop_id (resource id)
Copy the id and api for this integration to work.

![img1](https://user-images.githubusercontent.com/1471841/135556872-ff5b51ac-699e-4ea5-869c-f9b0d0c5b815.png)
![img2](https://user-images.githubusercontent.com/1471841/135556549-1cdd1621-9351-43d2-85d1-cb335f0b77ba.png)
![img3](https://user-images.githubusercontent.com/1471841/149643244-245c9a5a-cb0f-4de4-b641-631bcf7fe764.png)
