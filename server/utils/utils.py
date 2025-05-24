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
    result = client.models.embed_content(
        model="text-embedding-004",
        contents=content,
        config={
          'output_dimensionality': VEC_DIM,
        }
    )
    print("Genereated", len(result.embeddings), "embeddings")
    return result.embeddings