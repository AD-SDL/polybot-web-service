# Polybot

[![Build Status](https://travis-ci.com/materials-data-facility/polybot.svg?branch=master)](https://travis-ci.com/materials-data-facility/polybot)
[![Coverage Status](https://coveralls.io/repos/github/materials-data-facility/polybot/badge.svg?branch=master)](https://coveralls.io/github/materials-data-facility/polybot?branch=master)

A server for controlling the robot synthesis of thin-film polymeric materials.

## Installation

We describe our full environment using an Anaconda environment file,
[`environment.yml`](./environment.yml).
Install it by calling:

`conda env create --file environment.yml`

The package requirements are also listed in [`requirements.txt`](./requirements.txt),
which you can use to build the environment using `pip`:

`pip install -e .`

## Running Polybot

Activate the environment, if you used Anaconda,
and then call `./run.sh` to 
launch a server that is accessible from localhost only.

## Using Polybot

Polybot comes with a command line interface, also named "`polybot`".

At present, the only command is to upload data to the server:

`polybot upload experiment_name file.csv`

Call `polybot --help` to see the full list of operations.
