# Intro

A simple python script used to populate a set of elasticsearch indices with Energy markets data. The data are pulled from the [Greek Energy Exchange Group](https://www.enexgroup.gr) using their automated downloading infrastructure, which they provide freely (dont abuse their service please.)

This is the script behind the population of the Greek Energy folder in https://stats.uname.gr

# Installation

## Requirements

* python3
* openpyxl, requests, pytz python packages (installable by pip or a Linux Distribution's package manager)

## Globally

### Debian/Ubuntu and derivatives

```
$ sudo apt install python3-openpyxl python3-requests python3-pytz
```

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

This is will fetch the data for the various electricity and gas markets for the current day

More complex invocations allow for specifying the start and end date, the markets to fetch, the elasticsearch indices to use for each section and username/password if you have enabled RBAC on your elasticsearch cluster.

```
usage: enexgr.py [-h] [-H HOST] [-u USER] [-p PASSWORD] [--admin-user ADMIN_USER] [--admin-password ADMIN_PASSWORD] [--create-indices]
                 [--shards SHARDS] [--replicas REPLICAS] [-s START] [-e END] [-v] [--version]

Fetch DAM data and put into elastic

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
  --shards SHARDS       Number of shards for each Elasticsearch index. Requires elasticsearch admin access
  --replicas REPLICAS   Number of replicas for each Elasticsearch index. Requires elasticsearch admin access
  -s START, --start START
                        The start date. YYYY-MM-DD format
  -e END, --end END     The end date. YYYY-MM-DD format
  -v, --verbose         Increase verbosity. May be specified multiple times
  --version             show program's version number and exit
```

# systemd integration

2 simple system units are provided to facilitate automating the population of data in a timely manner. A service unit as well as a timer unit is provided. Depending on your installation you 'll want to either install them at a system level (`/etc/systemd/system/`) or at a user level (most likely `/home/<username>/.config/systemd/user/`). They will need some adapting probably.
