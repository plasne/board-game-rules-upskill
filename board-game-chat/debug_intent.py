from promptflow import tool


@tool
def debug_intent(input: str, output: str, chat_history: str) -> str:
    print("PROMPT (INPUT)")
    print(input)
    print("INTENT OUTPUT")
    print(output)
    print("CHAT HISTORY")
    print(chat_history)
    return ""
