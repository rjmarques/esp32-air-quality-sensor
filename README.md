# ESP32 Air Quality Sensor Kit

#### Table of Contents  
* [Motivation](#motivation)  
* [Sensors and MCU](#sensors-and-mcu)  
* [Circuit and PCB Design](#circuit-and-pcb-design)
* [Home Assistant](#home-assistant)
* [Prometheus](#prometheus)
* [Credits](#credits)

## Motivation

_Disclaimer: I am a complete noob in PCB design and digital circuits. This is a just a hobby project I cobbled together on my free time after a lot of reading and googling._

My main goal was to learn how to program an Arduino MCU (or equivalent) and have it integrate into my [Home Assistant](https://www.home-assistant.io) service (running locally on my LAN), which opens up a few automation possibilities. With this in mind, I figured being able get data from a few simple atmospheric/air sensors would be both practical and educational.

As a bonus, I wanted to be able to expose the metrics to [Prometheus](https://prometheus.io), and have a nice [Grafana](https://grafana.com/) dashboard to display it all.

## Sensors and MCU

The sensor list is as follows:

1. [SGP40 VOC sensor from DFRobot](https://www.dfrobot.com/product-2241.html)
2. [Plantower PMS5003 Air Quality Sensor](https://www.aqmd.gov/docs/default-source/aq-spec/resources-page/plantower-pms5003-manual_v2-3.pdf) (PM1.0, PM2.5 and PM10 particulates)
3. [MH-Z19B CO2 sensors](https://www.winsen-sensor.com/sensors/co2-sensor/mh-z19b.html)

As for the micro controller, I picked a [NodeMCU ESP32](https://nodemcu.readthedocs.io/en/dev-esp32/) because it was affordable, has WIFI, has all the connectors I needed, and crucially has good documentation online.

The code for the MCU can be found here: [main.ino](https://github.com/rjmarques/esp32-air-quality-sensor/blob/main/sketches/main/main.ino). I won't go into too much detail regarding the implementation here, but the main features are:

* Initialise all the sensors
* Periodically reading values from the sensors (using third-party libraries) and holding the data on memory
* Establish WiFi connectivity and periodically re-establish it if it's lost for whatever reason
* Expose a few REST endpoints (two in JSON, one in Prometheus format) that can be used by external services to get the latest sensor data.

Different sensors use different communication protocols, which affects which kinds of pins they need be connected to on the MCU. Additionally, not all pins should be used since they might be meant for internal use, or even be pulled high on boot (which can cause weird behaviour on your projects). The pinout for the MCU is:

![image](https://user-images.githubusercontent.com/19153038/156890923-1563c737-ce61-46bb-8bf0-d9a600f856c4.png)

A great video about the NodeMCU's pins can be found here: https://www.youtube.com/watch?v=c0tMGlJVmkw.

Essentially, I ended up going with the following pin selection:

1. **SGP40** uses I2C so I simply use the appropriate SDA (GPIO 21) and SCL (GPIO 22) pins on the MCU
2. **MH-Z19B** uses UART so I picked the hardware UART pins GPIO16 and GPIO17.
3. **PMS5003** also uses UART and since I have no good UART pins left I used the software serial library and pins GPIO32 and GPIO33

I don't power the MCU via its built-in micro-USB port, so I'm using the 5V and GND pins to drive the unit. More about this in the next section

One thing that perhaps will simplify your life a lot is to assign a static IP to the device, after it first connects to your home network. Otherwise, other services sevices that poll this device might suddenly lose connectivity, if you're unlucky with DHCP leasing.

## Circuit and PCB Design

I wanted to have the final result to look nice and not resemble a rat's nets of tiny wires. With this in mind I decided to design my own PCB would be the way to go. However, before I got to that stage, I needed to test the whole circuit, and code, on a breadboard. I used [EasyEDA](https://easyeda.com/) to design the circuit diagram. My final iteration looks like this:  

![image](https://user-images.githubusercontent.com/19153038/156892243-ff228656-c39f-4614-81be-3d52ceb94600.png)

The whole board is powered via a single micro-USB port connected to on/off physical switch. I added a few capacitors to the circuit to try and filter out any electrical noise going into the various sensors, albeit this is perhaps overkill. I also added some diodes to ensure some directionality on the circuit given that the 5V pin on the MCU powers on if you connect a cable to the MCU's USB port. I wanted to ensure that when I'm uploading firmware to the board all the sensors would be completely off.

From the circuit diagram, EasyEDA also allows you to design your own PCB and even allows you to export all the Gerber files that you later can use to actually pay someone to print the PCB for you. There's plenty of tutorials online for this so I won't go into detail here. One key thing is to ensure that the sizes actually match the components in real life, in particular the distance between pins or even the pin through-hole diameters. I mostly used uploaded PCB component footprints uploaded by DIY user, which work great for the most part but there's no guarantee they will be correct. The onus is on you to ensure this.

The PCB I designed looks like this:

![image](https://user-images.githubusercontent.com/19153038/156892634-a8840f3d-2508-4a30-9bfb-9ff74ed226f5.png)

I added some through-holes, for M3 bolts, on the corners of the PCB so I could later screw it onto an acrylic surface.

And the printed board itself:

<p float="left">
  <img src="https://user-images.githubusercontent.com/19153038/156892985-02cb76fc-2a73-4bad-a311-e03569dbdeb9.png" width=500>
  <img src="https://user-images.githubusercontent.com/19153038/156892986-fabe3274-fab9-46e9-974c-d16f8690367b.png" width=500>
</p>
  
Afterwards I put on my soldering hat and got busy:

<p float="left">
  <img src="https://user-images.githubusercontent.com/19153038/156893500-01c4bbd3-a034-4c29-88c2-4712e86b1496.jpg" width=500>
  <img src="https://user-images.githubusercontent.com/19153038/156893502-e11bdf9e-7e41-4997-9e44-d33eb5cf5ac0.jpg" width=500>
</p>

_Note: the PMS5003 is held onto the board with 4 M2.5 bolts._

## Home Assistant

The arduino sketch exposes two JSON REST endpoints that I used specifically for the integration with home assistant:

* `/` - exposes basic information about the board itself, including the chip ID and MAC address
* `/readings` - exposes the latest sensor readings

I then wrote the integration that can be found in the [customs component](https://github.com/rjmarques/esp32-air-quality-sensor/tree/main/custom_components/esp32_air_quality) folder. I'll leave the details of the home assistant programming model out of scope for this documentation. 

The key takeaways are that Home Assistant first adds the MCU as a _device_ and uniquely identifies it by a combination of chip ID and mac address. Which means you can have many of these boards around your house and home assistant would be able to track each one individually. Additionally, home assistant polls the device every so often to get new sensor readings and updates its internal sensor _entities_. You can then do whatever you want with these readings such as, simply displaying them, creating custom automations (e.g, notifying your phone to open the window of whatever room the device is associated to.), etc.

To get this integration into home assistant I used [HACS](https://hacs.xyz/). I simply added this repo into hacs, which is expecting to find integrations in the `custom_components` folder. Afterward I was able to find an integration called "ESP32 Air Quality" in home assistant's integration list. The integration asks you for your device's hostname or IP address, and verifies it can reach the device.

And then presto, your device is added onto home assistant

![image](https://user-images.githubusercontent.com/19153038/156894247-c87b228d-fdc1-4b92-bc32-5a15bb4cc708.png)

Afterwards you can start creating automations like a boss!

## Prometheus

I also added one additional REST endpoint (`/metrics`) that follows the key-value format that Prometheus understands. Consequently, you can easily add the device as a target in Prometheus. 

I'll leave that as an exercise to the reader, as well as integrating Prometheus into Grafana, and creating a dashboard for the device. 

My air quality monitoring dashboard looks like:

![image](https://user-images.githubusercontent.com/19153038/156894530-ddce4145-950a-49a9-97ed-898c1873f243.png)

## Credits

I took a lot of inspiration for the project from: 

* https://howtomechatronics.com/projects/diy-air-quality-monitor-pm2-5-co2-voc-ozone-temp-hum-arduino-meter/
* https://www.youtube.com/watch?v=Cmr5VNALRAg
