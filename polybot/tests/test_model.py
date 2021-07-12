"""Tests for the models"""


def test_generate_search_space(example_template):
    data = example_template.generate_search_space_dataframe()
    assert len(data.columns) == 15
    assert len(data["annealing_post.T"].value_counts()) == 1
    assert len(data["prepare_solution.V_sol[1]"].value_counts()) == 6
    assert len(data["coating_on_top.vel"].value_counts()) == 10


def test_generate_sample(example_template):
    example_template.create_new_sample()
