# Prometheus libvirt exporter

Prometheus libvirt exporter is tool for scraping metrics from libvirt daemon and exposing those metric in prometheus format

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

What things you need to install in case  

if you want to run exporter on host itself
```
python
libvirt-python==3.7.0
prometheus-client==0.0.21
```
if you want to run exporter in docker container
```
docker
docker-compose
```
### Installing

if you want to run exporter on host itself
```
git clone https://github.com/beylistan/prometheus_libvirt_exporter.git
pip install -r requirements.txt
```
if you want to run exporter in docker container
```
docker pull beylistan/prometheus_libvirt_exporter
```
### Running
if you want to run exporter on host itself
```
python prometheus_libvirt_exporter.py -si [scrape interval in seconds] -uri [Uniform Resource Identifier]
```
if you want to run exporter in docker container
```
docker run -i \                   
   -v /var/run/libvirt/libvirt-sock:/var/run/libvirt/libvirt-sock:Z prometheus_libvirt_exporter \
   python prometheus_libvirt_exporter.py -si [scrape interval in seconds] -uri [Uniform Resource Identifier]
```


