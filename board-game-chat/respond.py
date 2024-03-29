from promptflow import tool


@tool
def my_python_tool(action: str, chat_output: str) -> str:
    if action == "greet":
        return "Hello. I am a board game rules chatbot. How can I help you today?"
    elif action == "stop":
        return "I can only answer questions about board game rules."
    else:
        return chat_output
