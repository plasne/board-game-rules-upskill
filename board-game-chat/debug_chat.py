from promptflow import tool


@tool
def debug_chat(input: str) -> str:
    print("PROMPT (INPUT)")
    print(input)
    return ""
