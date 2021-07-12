# Bayesian Optimization

This example uses Bayesian Optimization to select the next best experiment.
For now, we hard-code a GPR model using RBF kernels and UCB for selecting the best experiment.

Inference tasks are run using Parsl, which can be configured to execute tasks on distributed compute.
For now, we implement a local version (see [`local_compute.py`](./local_compute.py)) as the computations
complete very quickly (~10s for 3 million inference tasks).

Launch using `polybot planner -p planner:BOPlanner -t local_compute:make_task_server opt_spec.yaml`.
