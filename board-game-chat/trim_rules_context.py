from promptflow import tool


@tool
def trim_rules_context(context: list) -> list:
    reranked = sorted(
        context, key=lambda value: value.get("search_score", 0), reverse=True
    )
    return reranked[:3]
