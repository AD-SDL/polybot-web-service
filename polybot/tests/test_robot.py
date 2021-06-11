from polybot.robot import send_new_sample


def test_submit(example_sample, fake_robot):
    send_new_sample(example_sample)
