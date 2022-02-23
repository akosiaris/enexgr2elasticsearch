# Intro

A simple python script used to populate a set of 3 elasticsearch indices with Energy markets data. The data are pulled from the [Greek Energy Exchange Group](https://enexgroup.gr) using their automated downloading infrastructure (they are kind to be open and provide them freely, don't abuse their service please.)

This is the script behind the population of the Energy folder in https://stats.uname.gr

# Installation

Hasn't been released as a python package yet, git clone for now

## Requirements

* python3
* openpyxl, requests, pytz python packages (installable by pip or a Linux Distribution's package manager)

## Creation of the elasticsearch indices

You 'll want to either install python requirements globally or in a virtualenv

```
python3 -m venv .venv
. .venv/bin/activate
pip3 install -r requirements.txt
```

# Usage

Simplest form is:

`python3 enexgr2elasticsearch.py`

This is will fetch the data for the 4 markets and the 3 sections for the current day.

More complex invocations allow for specifying the start and end date, the markets to fetch, the elasticsearch indices to use for each section and username/password if you have enabled RBAC on your elasticsearch cluster.

```

usage: enexgr.py [-h] [-s START] [-e END] [-v] [--version]

Fetch DAM data and put into elastic

optional arguments:
  -h, --help            show this help message and exit
  -s START, --start START
                        The start date. YYYY-MM-DD format
  -e END, --end END     The end date. YYYY-MM-DD format
  -v, --verbose         Increase verbosity. May be specified multiple times
  --version             show program's version number and exit

```

# systemd

2 simple system units are provided to facilitate automating the population of data in a timely manner. A service unit as well as a timer unit is provided. Depending on your installation you 'll want to either install them at a system level (`/etc/systemd/system/`) or at a user level (most likely `/home/<username>/.config/systemd/user/`)


