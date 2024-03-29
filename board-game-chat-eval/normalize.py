from promptflow import tool
import json


def extract_json(payload: str) -> str:
    start = payload.find("{")
    end = payload.rfind("}") + 1
    return payload[start:end]


@tool
def normalize(groundedness: str, relevancy: str, coherance: str) -> str:
    jgrd = json.loads(extract_json(groundedness))
    jrel = json.loads(extract_json(relevancy))
    jcoh = json.loads(extract_json(coherance))
    return {
        "groundedness": jgrd["score"],
        "relevance": jrel["score"],
        "coherance": jcoh["score"],
    }
