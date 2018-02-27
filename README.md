# air-monitoring-scripts
Learning python by getting air quality data from various providers. For some of thos provider you will need to provide API key obtained from them, also keep in mind their API limits.
You can put in your location, and how far from it you want to find sensors (`DISTANCE_DG`). Currently this is in degrees, since apparently calculating degrees from distance is a non-trivial problem. I found `0.025` give me sensors up to about `2.5 km` away, which works nicely for me. If you provide a separate value for that in `[gios]` section (since there are less of those), that value will be used, otherwise the default value from `[location]` will be used.
## airly.py
You'll need API key from them, and if you query them more than `1009 requests / day and 53 request / minute` they may suspend your account.
## gios.py
They ask to not query them more often than twice an hour.
## waqi
WIP
## purifier.py
https://python-miio.readthedocs.io/en/latest/discovery.html#device-discovery etc.
