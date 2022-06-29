# Script for monitoring home network
Script writen for using into non-stable networks for normal work hotspot.
Script analizing network devices and local network, ping 8.8.8.8 and local ip with best avg ping.
If droped packages or avg ping > 100 then rebooted needed network.
All doing writen to network_monitoring.log into network_monitoring.py directory.
###### Warning! Made for home purposes only. Use at own risk.
## Preparing:
`git clone https://github.com/Melhin8/network_monitor.git`

## Using:
Run `python3 network_monitoring.py`.
You can add this comand to Startup Applications Utility, for autostart with system.