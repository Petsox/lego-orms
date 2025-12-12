dependencies:
    Flask
    adafruit-circuitpython-pca9685
    adafruit-circuitpython-servokit

Create /etc/systemd/system/lego-hotspot.service with the following contents:

[Unit]
Description=LEGO-ORMS Hotspot Manager
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/LEGO-ORMS/web
ExecStart=/<YOUR_USER>/bin/python3 /<PATH_TO_wifi.py>
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target