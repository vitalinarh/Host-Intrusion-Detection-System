# Device Behaviour Monitoring

This repository hosts the development of a Device Behaviour Monitoring system carried out in the scope of the ARCADIAN-IoT - Autonomous Trust, Security and Privacy Management Framework for IoT, Grant Agreement Number:101020259. H2020-SU-DS02-2020.

This work's goal is to implement a Intusion Detection System based on system call analysis for IoT devices, while relying on Federated Learning techniques to update the AI models.

## Table of contents

* [Requirements](#requirements)
* [Getting started](#getting-started)
    * [Ubuntu](#ubuntu)
    * [Kali Linux](#kali-linux)
    * [CentOS](#centos)
* [Configuration](#configuration)
* [Troubleshooting](#troubleshooting)
* [FAQ](#faq)
* [Authors and acknowledgment](#authors-and-acknowledgment)
* [License](#License)
* [Project status](#project-status)

## Requirements

This module requires the following modules:

- Python: version >= 3.6
- Perf Linux Tool

## Getting started 

A quick introduction of the minimal setup you need to get the program running.

### Ubuntu

Change to root
```shell
sudo -i
```

First make sure that your system is up to date
```shell
apt update && sudo apt upgrade -y
```

Download the repository
```shell
git clone https://github.com/vitalinarh/device_behaviour_monitoring
```

Change to repository folder
```shell
cd device_behaviour_monitoring
```

Install Perf Linux tool for system call log extraction:
```shell
apt install linux-tools-generic -y
```

Install the python virtual environment module:
```shell
apt install virtualenv python3-venv -y
```

Create a virtual environment:
```shell
python3 -m venv env 
```

Activate the virtual environment:
```shell
. $PWD/env/bin/activate
```

Install python requirements:
```shell
python3 -m pip install -r requirements.txt
```

Run the script
```
python3 dbm.py
```

If you want to create an executable:
```shell
python3 -m pio install pyinstaller
python3 -m pip install --upgrade pyinstaller
python3 -m PyInstaller -F dbm.py --hidden-import="sklearn.metrics._pairwise_distances_reduction._datasets_pair" --hidden-import="sklearn.metrics._pairwise_distances_reduction._middle_term_computer" --exclude-module _bootlocale
```

Change the executable directory to the main project folder
```shell
mv $PWD/dist/dbm ./
```

Execute the binary
```shell
./dbm
```

### Kali Linux

Change to root
```shell
sudo -i
```

First make sure that your system is up to date
```shell
apt update && sudo apt upgrade -y
```

Download the repository
```shell
git clone https://github.com/vitalinarh/device_behaviour_monitoring
```

Change to repository folder
```shell
cd device_behaviour_monitoring
```

Install Perf Linux tool for system call log extraction:
```shell
apt install linux-perf -y
```

Install the python virtual environment module:
```shell
apt install python3-virtualenv -y
```

Create a virtual environment:
```shell
python3 -m venv env 
```

Activate the virtual environment:
```shell
. $PWD/env/bin/activate
```

Install python requirements:
```shell
python3 -m pip install -r requirements.txt
```

Run the script
```
python3 dbm.py
```

If you want to create an executable:
```shell
python3 -m pio install pyinstaller
python3 -m pip install --upgrade pyinstaller
python3 -m PyInstaller -F dbm.py --hidden-import="sklearn.metrics._pairwise_distances_reduction._datasets_pair" --hidden-import="sklearn.metrics._pairwise_distances_reduction._middle_term_computer" --exclude-module _bootlocale
```

Change the executable directory to the main project folder
```shell
mv $PWD/dist/dbm ./
```

Execute the binary
```shell
./dbm
```

### CentOS 7

Change to root
```shell
sudo -i
```

First make sure that your system is up to date
```shell
yum -y upgrade
```

Download the repository
```shell
git clone https://github.com/vitalinarh/device_behaviour_monitoring
```

Change to repository folder
```shell
cd device_behaviour_monitoring
```

Install Perf Linux tool for system call log extraction:
```shell
yum install perf -y
```

Install the python virtual environment module:
```shell
yum install python3-virtualenv
```

Create a virtual environment:
```shell
python3 -m virtualenv env
```

Activate the virtual environment:
```shell
. $PWD/env/bin/activate
```

Install python requirements:
```shell
python3 -m pip install -r requirements.txt
```

Run the script
```
python3 dbm.py
```

If you want to create an executable:
```shell
python3 -m pio install pyinstaller
python3 -m pip install --upgrade pyinstaller
python3 -m PyInstaller -F dbm.py --hidden-import="sklearn.metrics._pairwise_distances_reduction._datasets_pair" --hidden-import="sklearn.metrics._pairwise_distances_reduction._middle_term_computer" --exclude-module _bootlocale
```

Change the executable directory to the main project folder
```shell
mv $PWD/dist/dbm ./
```

Execute the binary
```shell
./dbm
```

## Installing Federated Server Application (Ubuntu)

This module is to be installed and run on a remote server.
Assuming that you have installed Docker and it is running.

Build the image
```shell
docker build -t server federated/Server/ 
```
Run the image's default command, which should start everything up.
```shell
docker run -it -p 9898:9898 server
```

Example of how it should look from the server side with one client:

<img src="https://i.ibb.co/yqc5VYy/Screenshot-2023-03-10-at-11-58-15.png" width="850"/>

## Configuration

Environment variables can be set up and customized in the .env file (/trace_module folder).

For RabbitMQ communication with other ARCADIAN-IoT components, we need to setup of the next variables:

```
HOST
PORT
VIRTUAL_HOST
CREDENTIALS_USERNAME
CREDENTIALS_PASSWORD
ROUTING_KEY
EXCHANGE_KEY
```

Other variables can also be changed and calibrated:

Threshold value for intrusion detection (value needs to be from 0 to 1). Default value is 0.5
```
DETECTION_THRESHOLD
````

Maximum of system calls in queue before pausing the tracer. Default value is 25000.
```
SYSCALL_LIMIT
```

Cooldown time (in seconds) for the tracer before resuming the syscall tracing. Default value is 30 seconds.
```
PAUSE_TIME
```

Flag to save or not syscalls in data folder. 1 is to enable the syscalls being saved on /data folder, any other value is to disable.
```
SAVE_SYSCALLS
```

## Troubleshooting
WIP

## FAQ

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
