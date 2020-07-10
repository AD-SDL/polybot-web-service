# Polybot

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
