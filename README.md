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

Configure the web service and planner using environment variables, which can be stored in the `.env` file in the run directory.
Key variables include:

- `ROBOT_URL`: URL of the Robot Scheduler
- `REDIS_URL`: URL of the Redis queue
- `LOG_NAME`: Name of the log file

Full options are in [`polybot/config.py`](./polybot/config.py).

An "optimization specification" JSON file (note `opt_spec.json` above) provides additional details to the AI planning algorithm.
The specification includes the names of input variables and a path to a template workflow.
The `OptimizationProblem` specification in [`polybot/planning.py`](./polybot/planning.py) includes the full details.

### Designing Planning Algorithms

The default AI planning algorithm randomly selects a new experiment from the search space once a previous experiment completes,
but there is significant flexibility to write more complex algorithms.
Define a new planning algorithm by implementing a new `BasePlanner` and supplying a path to that file when launching polybot.
For example, use a planning class named `BOPlanner` stored in a python file named `planner.py` by calling

```bash
polybot planner --planning-class planner:BOPlanner
```

Polybot uses [Colmena](http://colmena.rtfd.org/) to express planning algorithms.
We'll include more details and examples on how to make Colmena work for planning robotic experiments as we learn more.
