from promptflow import tool
import json


@tool
def normalize(groundedness: str, relevancy: str, coherance: str) -> str:
    jgrd = json.loads(groundedness)
    jrel = json.loads(relevancy)
    return {
        "groundedness": jgrd["score"],
        "relevance": jrel["score"],
        "coherance": int(coherance),
    }
