# Polybot

[![Python package](https://github.com/AD-SDL/polybot-web-service/actions/workflows/python-package.yml/badge.svg)](https://github.com/AD-SDL/polybot-web-service/actions/workflows/python-package.yml)
[![Coverage Status](https://coveralls.io/repos/github/AD-SDL/polybot-web-service/badge.svg?branch=master)](https://coveralls.io/github/AD-SDL/polybot-web-service?branch=master)

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

The web service is built from three smaller services.

- Redis: Launch Redis as normal: `redis-server`
- Web Service: Launch FastAPI using Uvicorn: `uvicorn polybot.fastapi:app`
- AI planner: Launch using the CLI: `polybot planner opt_spec.json`

### Configuring PolyBot

The web service and planner are configured using environment variables, which can be stored in the `.env` file in the run directory.
Key variables include:

- `ROBOT_URL`: URL of the Robot Scheduler
- `REDIS_URL`: URL of the Redis queue
- `LOG_NAME`: Name of the log file

Full options are in [`polybot/config.py`](./polybot/config.py).

The planning agent is also configured using an "optimization specification" JSON file (note `opt_spec.json` above).
The specification includes the names of input variables and a definition of a template workflow specification.
Full details are expressed in the `OptimizationProblem` speficiation in [`polybot/planning.py`](./polybot/planning.py).
