# Bayesian Optimization

This example uses Bayesian Optimization to select the next best experiment.
For now, we hard-code a GPR model using RBF kernels and EI for selecting the best experiment.
All computations are run locally.

Launch using `polybot planner -p planner:BOPlanner opt_spec.json`
