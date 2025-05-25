import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv(".env.local")


VEC_DIM = 768


def get_embedding(content: list[str]|str) -> list[types.ContentEmbedding]:
    """
    Get the embedding of a given text from gemini
    """
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    _results = []
    if isinstance(content, str):
        print("Generating embedding for single content")
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=[content],
            config={
                'output_dimensionality': VEC_DIM,
            }
        )
        print("Generated", len(result.embeddings), "embeddings")
        return result.embeddings
    if isinstance(content, list) and len(content) > 100:
        batches = into_batches(content)
        for batch in batches:
            if len(batch) == 0:
                continue
            print("Generating embeddings for batch of size", len(batch))
            result = client.models.embed_content(
                model="text-embedding-004",
                contents=batch,
                config={
                'output_dimensionality': VEC_DIM,
                }
            )
            print("Generated", len(result.embeddings), "embeddings")
            _results.extend(result.embeddings)
    return _results


def into_batches(input_list: list[str], slice_length: int = 100) -> list[list[str]]:
    """
    Splits a list into smaller lists of a specified length.
    Args:
        input_list (list): The list to be split.
        slice_length (int): The length of each sublist.
    """
    return [input_list[i:i + slice_length] for i in range(0, len(input_list), slice_length)]
