import json
import re
import requests
from promptflow import tool
from promptflow.connections import AzureOpenAIConnection
from promptflow.connections import CognitiveSearchConnection

field_map = {
    "id": ["id"],
    "url": ["url", "uri", "link", "document_link"],
    "filepath": ["filepath", "filename"],
    "content": ["chunk"],
}
title_regex = re.compile(r"title: (.*)\n")


def get_if_string(doc, fieldName):
    try:
        value = doc.get(fieldName)
        if isinstance(value, str) and len(value) > 0:
            return value
        return None
    except:
        return None


def get_truncated_string(string_value, max_length):
    return string_value[:max_length]


def get_title(doc):
    max_title_length = 150
    title = get_if_string(doc, "title")
    if title:
        return get_truncated_string(title, max_title_length)
    else:
        title = get_if_string(doc, "content")
        if title:
            titleMatch = title_regex.search(title)
            if titleMatch:
                return get_truncated_string(titleMatch.group(1), max_title_length)
            else:
                return None
        else:
            return None


def get_chunk_id(doc):
    chunk_id = get_if_string(doc, "chunk_id")
    return chunk_id


def get_search_score(doc):
    try:
        return doc["@search.rerankerScore"]
    except:
        return None


def process_search_docs_response(docs):
    outputs = []
    for doc in docs:
        formatted_doc = {}
        for fieldName in field_map.keys():
            for fromFieldName in field_map[fieldName]:
                fieldValue = get_if_string(doc, fromFieldName)
                if fieldValue:
                    formatted_doc[fieldName] = doc[fromFieldName]
                    break
        formatted_doc["title"] = get_title(doc)
        formatted_doc["chunk_id"] = get_chunk_id(doc)
        formatted_doc["search_score"] = get_search_score(doc)
        outputs.append(formatted_doc)
    return outputs


def get_query_embedding(
    query, endpoint, api_key, api_version, embedding_model_deployment
):
    request_url = f"{endpoint}/openai/deployments/{embedding_model_deployment}/embeddings?api-version={api_version}"
    headers = {"Content-Type": "application/json", "api-key": api_key}
    request_payload = {"input": query}
    embedding_response = requests.post(
        request_url, json=request_payload, headers=headers, timeout=None
    )
    if embedding_response.status_code == 200:
        data_values = embedding_response.json()["data"]
        embeddings_vectors = [data_value["embedding"] for data_value in data_values]
        return embeddings_vectors
    else:
        raise Exception(f"failed to get embedding: {embedding_response.json()}")


def search_query_api(
    endpoint,
    api_key,
    api_version,
    index_name,
    query_type,
    query,
    filter,
    top_k,
    embedding_model_connection,
    embedding_model_name=None,
    semantic_configuration_name=None,
    vector_fields=None,
):
    request_url = (
        f"{endpoint}/indexes/{index_name}/docs/search?api-version={api_version}"
    )
    request_payload = {
        "top": top_k,
        "select": "title, chunk_id, chunk, game_name, edition",
        "search": query,
    }
    if filter:
        request_payload["filter"] = filter
    if query_type == "simple":
        request_payload["queryType"] = query_type
        pass
    elif query_type == "semantic":
        request_payload["queryType"] = query_type
        request_payload["semanticConfiguration"] = semantic_configuration_name
        request_payload["answers"] = "extractive|count-3"
    elif query_type in ("vector", "vectorSimpleHybrid", "vectorSemanticHybrid"):
        if vector_fields:
            query_vectors = get_query_embedding(
                query,
                embedding_model_connection["api_base"],
                embedding_model_connection["api_key"],
                embedding_model_connection["api_version"],
                embedding_model_name,
            )
            payload_vectors = [
                {
                    "vector": query_vector,
                    "fields": vector_fields,
                    "k": top_k,
                    "kind": "vector",
                }
                for query_vector in query_vectors
            ]
            request_payload["vectorQueries"] = payload_vectors

        if query_type == "vectorSimpleHybrid":
            request_payload["queryType"] = "simple"
            pass
        elif query_type == "vectorSemanticHybrid":
            request_payload["queryType"] = "semantic"
            request_payload["semanticConfiguration"] = semantic_configuration_name
    else:
        raise Exception(f"unsupported query type: {query_type}")

    headers = {"Content-Type": "application/json", "api-key": api_key}
    retrieved_docs = requests.post(
        request_url, json=request_payload, headers=headers, timeout=None
    )
    if retrieved_docs.status_code == 200:
        return process_search_docs_response(retrieved_docs.json()["value"])
        # return retrieved_docs.json()["value"]
    else:
        raise Exception(f"failed to query search index : {retrieved_docs.json()}")


@tool
def get_rules_context(
    intent: str,
    search_connection: CognitiveSearchConnection,
    index_name: str,
    query_type: str,
    top_k: int,
    semantic_configuration: str,
    vector_fields: str,
    embedding_model_connection: AzureOpenAIConnection,
    embedding_model_name: str,
) -> list:
    semantic_configuration = (
        semantic_configuration if semantic_configuration != "None" else None
    )
    vector_fields = vector_fields if vector_fields != "None" else None
    embedding_model_name = (
        embedding_model_name if embedding_model_name != None else None
    )

    # convert intent from string to json
    payload = json.loads(intent)

    # determine filter
    filter = None
    if payload["game_name"] and payload["edition"]:
        filter = f"game_name eq '{payload['game_name']}' and edition eq '{payload['edition']}'"
    elif payload["game_name"]:
        filter = f"game_name eq '{payload['game_name']}'"
    elif payload["edition"]:
        filter = f"edition eq '{payload['edition']}'"

    # search
    all_outputs = [
        search_query_api(
            search_connection["api_base"],
            search_connection["api_key"],
            search_connection["api_version"],
            index_name,
            query_type,
            query,
            filter,
            top_k,
            embedding_model_connection,
            embedding_model_name,
            semantic_configuration,
            vector_fields,
        )
        for query in payload["search_queries"]
    ]

    # trim response
    included_outputs = []
    while all_outputs and len(included_outputs) < top_k:
        for output in list(all_outputs):
            if len(output) == 0:
                all_outputs.remove(output)
                continue
            value = output.pop(0)
            if value not in included_outputs:
                included_outputs.append(value)
                if len(included_outputs) >= top_k:
                    break
    return included_outputs
