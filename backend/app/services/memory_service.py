import uuid
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.memory import MemoryItem
from app.services.embedding import get_embedding

logger = logging.getLogger(__name__)


class MemoryService:
    async def save(
        self,
        db: AsyncSession,
        content: str,
        memory_type: str,
        prospect_id: Optional[uuid.UUID] = None,
        metadata: Optional[dict] = None,
    ) -> MemoryItem:
        # Embedding is best-effort — save without it if the API is unavailable
        try:
            embedding = await get_embedding(content)
        except Exception as e:
            logger.warning(f"[MemoryService] Embedding failed, saving without vector: {e}")
            embedding = None

        item = MemoryItem(
            prospect_id=prospect_id,
            memory_type=memory_type,
            content=content,
            embedding=embedding,
            metadata_=metadata or {},
        )
        db.add(item)
        await db.flush()
        return item

    async def search(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = 5,
        prospect_id: Optional[uuid.UUID] = None,
        memory_type: Optional[str] = None,
    ) -> List[MemoryItem]:
        """Semantic search over memory using pgvector cosine similarity.
        Falls back to an empty list if the embedding API is unavailable."""
        try:
            query_embedding = await get_embedding(query)
        except Exception as e:
            logger.warning(f"[MemoryService] Embedding failed for search, skipping memory: {e}")
            return []

        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # Always exclude rows with NULL embeddings from vector search
        filters = ["embedding IS NOT NULL"]
        params = {"embedding": embedding_str, "top_k": top_k}

        if prospect_id:
            filters.append("prospect_id = :prospect_id")
            params["prospect_id"] = str(prospect_id)
        if memory_type:
            filters.append("memory_type = :memory_type")
            params["memory_type"] = memory_type

        where_clause = "WHERE " + " AND ".join(filters)

        sql = text(
            f"""
            SELECT id, prospect_id, memory_type, content, metadata, created_at,
                   1 - (embedding <=> :embedding::vector) AS similarity
            FROM memory_items
            {where_clause}
            ORDER BY embedding <=> :embedding::vector
            LIMIT :top_k
            """
        )

        result = await db.execute(sql, params)
        rows = result.mappings().all()

        items = []
        for row in rows:
            item = MemoryItem(
                id=row["id"],
                prospect_id=row["prospect_id"],
                memory_type=row["memory_type"],
                content=row["content"],
                metadata_=row["metadata"],
                created_at=row["created_at"],
            )
            items.append(item)
        return items

    async def get_prospect_history(
        self, db: AsyncSession, prospect_id: uuid.UUID
    ) -> List[MemoryItem]:
        result = await db.execute(
            select(MemoryItem)
            .where(MemoryItem.prospect_id == prospect_id)
            .order_by(MemoryItem.created_at.desc())
            .limit(20)
        )
        return list(result.scalars().all())


memory_service = MemoryService()
