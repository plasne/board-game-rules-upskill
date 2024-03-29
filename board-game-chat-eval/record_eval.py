from promptflow import tool
import requests
import json


@tool
def record_eval(eval_set: str, eval_desc: str, evals: dict) -> str:
    url = "http://host.docker.internal:6010/api/projects/project-01/experiments/pelasne-01/results"
    headers = {"Content-Type": "application/json"}
    data = {
        "set": eval_set,
        "description": eval_desc,
        "metrics": {
            "gpt-coherance": {"value": evals["coherance"]},
            "gpt-relevance": {"value": evals["relevance"]},
            "gpt-groundedness": {"value": evals["groundedness"]},
        },
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.status_code
