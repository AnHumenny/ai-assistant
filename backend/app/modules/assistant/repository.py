from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.assistant.models.knowledge import KnowledgeDocument


async def search_similar_documents(
    session: AsyncSession,
    embedding: list[float],
    limit: int = 5,
) -> list[tuple[KnowledgeDocument, float]]:
    """Return (document, cosine_similarity) pairs, most similar first."""

    distance = KnowledgeDocument.embedding.cosine_distance(embedding)

    statement = (
        select(KnowledgeDocument, distance.label("distance"))
        .where(KnowledgeDocument.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    )

    result = await session.execute(statement)

    return [(doc, 1.0 - float(dist)) for doc, dist in result.all()]
