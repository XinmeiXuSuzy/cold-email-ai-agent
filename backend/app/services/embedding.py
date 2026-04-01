from typing import List
import litellm
from app.config import settings


async def get_embedding(text: str) -> List[float]:
    """Generate a text embedding using LiteLLM."""
    response = await litellm.aembedding(
        model="text-embedding-3-small",
        input=[text],
        api_key=settings.openai_api_key,
    )
    return response.data[0]["embedding"]


async def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts."""
    response = await litellm.aembedding(
        model="text-embedding-3-small",
        input=texts,
        api_key=settings.openai_api_key,
    )
    return [item["embedding"] for item in response.data]
