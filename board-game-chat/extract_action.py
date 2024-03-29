from promptflow import tool
import json


@tool
def extract_action(intent: str) -> str:
    payload = json.loads(intent)
    if "action" in payload:
        return payload["action"]
    return "continue"
