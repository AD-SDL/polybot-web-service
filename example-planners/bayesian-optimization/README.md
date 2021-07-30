# Bayesian Optimization

This example uses Bayesian Optimization to select the next best experiment.
For now, we hard-code a GPR model using RBF kernels and UCB for selecting the best experiment.

Inference tasks are run using Parsl, which can be configured to execute tasks on distributed compute.
For now, we implement a local version (see [`local_compute.py`](./local_compute.py)) as the computations
complete very quickly (~10s for 3 million inference tasks).

Launch using `polybot planner -p planner:BOPlanner -t local_compute:make_task_server opt_spec.yaml`.

We recommend also launching the FastAPI services from this folder as well so that it uses the same environment variables.

## Tailoring to your system

First, edit the `.env` file in this folder to point to the proper address for the robot and a good path for storing samples.

## Launching the Services

1. Start up Redis
2. Launch the HTTP service for receiving new samples. (Linux: `../../run.sh`, Windows: `..\..\run.bat`)
3. Launch the planner using the `polybot` command listed above

Make sure to record the IP address and port number for your HTTP service,
which are needed to configure where the robot should send new data.
