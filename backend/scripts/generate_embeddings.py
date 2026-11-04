import asyncio

from sqlalchemy import select

from backend.app.core.db.session import async_session_factory
from backend.app.core.embedding import embedding_client
from backend.app.modules.assistant.models.knowledge import KnowledgeDocument


async def generate_embeddings() -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.embedding.is_(None))
        )

        documents = result.scalars().all()

        for document in documents:
            text = f"{document.name}. {document.description}"

            document.embedding = embedding_client.create_embedding(text)

            print(f"Embedded: {document.id} - {document.name}")

        await session.commit()

    print(f"Generated embeddings for {len(documents)} documents.")


if __name__ == "__main__":
    asyncio.run(generate_embeddings())
