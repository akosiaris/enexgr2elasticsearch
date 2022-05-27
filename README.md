# Intro

A simple python script used to populate a set of elasticsearch indices with Energy markets data. The data are pulled from the [Greek Energy Exchange Group](https://www.enexgroup.gr) using their automated downloading infrastructure, which they provide freely (dont abuse their service please.)

This is the script behind the population of the Greek Energy folder in https://stats.uname.gr

# Installation

## Requirements

* python3
* openpyxl, structlog, ecs-logging, requests, pytz python packages (installable by pip or a Linux Distribution's package manager)

## Globally

### Debian/Ubuntu and derivatives

```
$ sudo apt install python3-openpyxl python3-requests python3-pytz python3-structlog
```

Note that ecs-logging isn't packaged for Debian yet. You 'll need to install that via pip

### In a python virtual environemnt (venv)

You 'll want to either install python requirements globally or in a virtualenv

```
python3 -m venv .venv
. .venv/bin/activate
pip3 install -r requirements.txt
```

# Usage

Simplest form is:

`python3 enexgr2elasticsearch.py`

This is will fetch the data for the various electricity and gas markets for yesterday, today and tomorrow (at least for the Day Ahead Market)

More complex invocations allow for specifying the start and end date, username/password if you have enabled RBAC on your elasticsearch cluster, automatic creation of indices as well as a simplistic cache

```
usage: enexgr.py [-h] [-H HOST] [-u USER] [-p PASSWORD] [--admin-user ADMIN_USER] [--admin-password ADMIN_PASSWORD] [--create-indices] [--create-indices-shards SHARDS] [--create-indices-replicas REPLICAS] [-s START] [-e END] [-c CACHE] [-v] [--ecs-logging]
                 [--ecs-logging-endpoint ECS_LOGGING_ENDPOINT] [--version]

Fetch enexgroup.gr data and put into Elasticsearch

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  URL pointing to the elasticsearch cluster
  -u USER, --user USER  Elasticsearch user to write data
  -p PASSWORD, --password PASSWORD
                        Elasticsearch user password
  --admin-user ADMIN_USER
                        Elasticsearch admin user to create the indices
  --admin-password ADMIN_PASSWORD
                        Elasticsearch admin user password
  --create-indices      Create Elasticsearch indices. Requires elasticsearch admin access
  --create-indices-shards SHARDS
                        Number of shards for each newly created Elasticsearch index. Used only when creating indices. Defaults to 1. Requires elasticsearch admin access
  --create-indices-replicas REPLICAS
                        Number of replicas for each newly created Elasticsearch index. Used only when creating indices. Defaults to 0. Requires elasticsearch admin access
  -s START, --start START
                        The start date. YYYY-MM-DD format. Defaults to yesterday
  -e END, --end END     The end date. YYYY-MM-DD format. Defaults to tomorrow
  -c CACHE, --cache CACHE
                        Directory to be used as R/W cache for .xlsx files
  -v, --verbose         Increase verbosity. May be specified multiple times
  --ecs-logging         Use Elastic Common Schema logging. If --ecs-logging-endpoint is also configured, logs will be sent there via Elasticsearch REST index API. Otherwise, stdout will be used
  --ecs-logging-endpoint ECS_LOGGING_ENDPOINT
                        An ECS compatible Elasticsearch index endpoint, without the scheme (e.g. http://). A valid value would be "localhost:9200/logs-enexgr2elasticsearch-1/" which uses the post 7.16 built-in elasticsearch "logs-*-*" Data Stream. WARNING: The behavior is very
                        simplistic and crude. If you want proper handling of logs, invest in a proper log collector
  --version             show program's version number and exit
```

# Cache

Not really a proper cache, just a directory that fetched xlsx files will be stored in. Can also be manually prepopulated by downloading the Energy Exchange's zip bundles and unzipping them in here. That should allow saving some bandwidth for both sides

# systemd integration

2 simple system units are provided to facilitate automating the population of data in a timely manner. A service unit as well as a timer unit is provided. Depending on your installation you 'll want to either install them at a system level (`/etc/systemd/system/`) or at a user level (most likely `/home/<username>/.config/systemd/user/`). They will need some adapting probably.

# Docker

A Dockerfile is provided so you can build images and a docker-compose file to facilitate development. Those aren't currently targeted for anything else than development, don't rely on them much

# mkosi

mkosi files are provided too, to allow for building a systemd portable service image. Not targetted yet either for anything else than development
