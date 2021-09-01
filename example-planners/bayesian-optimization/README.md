# Bayesian Optimization

This example uses Bayesian Optimization to select the next best experiment.
For now, we hard-code a GPR model using RBF kernels and UCB for selecting the best experiment.

Inference tasks are run using Parsl, which can be configured to execute tasks on distributed compute.
For now, we implement a local version (see [`local_compute.py`](./local_compute.py)) as the computations
complete very quickly (~10s for 3 million inference tasks).

Launch using `polybot planner -p planner:BOPlanner -t local_compute:make_task_server opt_spec.yaml`.

## Tailoring to your system

First, edit the `.env` file in this folder to point to the proper address for the robot 
and the Study ID for the collection of completed samples in the Argonne Data cloud.

## Launching the Services

1. Start up Redis (e.g., run `redis-server` in another screen or terminal)
2. Launch the planner using the `polybot` command listed above

The planner will then run until you kill it with <kbd>Ctrl</kbd>+<kbd>C</kbd>.
