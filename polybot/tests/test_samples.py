from polybot.sample import load_samples

example_output = {
    "study": {
        "id": "U3R1ZHlOb2RlOjU=",
        "name": "polybot-ai-test",
        "description": "Test study for developing the Polybot AI planning service.",
        "keywords": [],
        "startDate": None,
        "status": "NEW",
        "created": "2021-08-30T16:54:41.706854+00:00",
        "updated": "2021-08-30T16:54:42.127315+00:00",
        "permissions": [
            {
                "user": {
                    "id": "VXNlck5vZGU6NQ==",
                    "name": "",
                    "email": "loganw@uchicago.edu"
                },
                "level": "ADMIN"
            }
        ],
        "investigations": [],
        "samples": []
    }
}


def test_load(example_sample):
    samples = list(load_samples())
    assert len(samples) >= 1
