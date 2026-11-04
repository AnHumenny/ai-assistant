import asyncio

from backend.app.core.db.session import async_session_factory
from backend.app.core.embedding import embedding_client
from backend.app.modules.assistant.repository import search_similar_documents


async def main() -> None:
    query = "Доставка заказа 1842"    #тестовые значения

    query_embedding = embedding_client.create_embedding(query)

    async with async_session_factory() as session:
        documents = await search_similar_documents(
            session=session,
            embedding=query_embedding,
            limit=5,
        )

    print(f"\nЗапрос: {query}\n")
    print("Наиболее похожие документы:\n")

    for document, similarity in documents:
        print(f"- {document.name}  (sim={similarity:.3f})")
        print(f"  Категория: {document.category}")
        print(f"  {document.description}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
