import logging
from backend.rag.pipeline import rag_pipeline
from backend.retrieval.vector_store import vector_store
from backend.database.session import init_db, upsert_company_profile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

def seed_database():
    """Pre-ingest reports for top tech and automotive companies into ChromaDB and SQLite."""
    logger.info("Initializing SQLite database...")
    init_db()

    seed_tickers = [
        ("AAPL", "Apple Inc.", "Technology", "Consumer Electronics"),
        ("MSFT", "Microsoft Corporation", "Technology", "Software Infrastructure"),
        ("NVDA", "NVIDIA Corporation", "Technology", "Semiconductors"),
        ("GOOGL", "Alphabet Inc.", "Technology", "Internet Content & Information"),
        ("AMZN", "Amazon.com Inc.", "Consumer Cyclical", "Internet Retail"),
        ("TSLA", "Tesla Inc.", "Consumer Cyclical", "Auto Manufacturers"),
        ("META", "Meta Platforms Inc.", "Technology", "Internet Content & Information")
    ]

    total_chunks = 0
    for ticker, name, sector, industry in seed_tickers:
        logger.info(f"Seeding data for {name} ({ticker})...")
        count = rag_pipeline.ensure_ticker_ingested(ticker, years=[2023, 2024, 2025])
        total_chunks += count
        upsert_company_profile(
            ticker=ticker,
            name=name,
            sector=sector,
            industry=industry,
            docs_count=vector_store.get_collection_count()
        )
        logger.info(f"Ingested {count} chunks for {ticker}.")

    logger.info(f"Seeding completed! Total vector DB chunks count: {vector_store.get_collection_count()}")

if __name__ == "__main__":
    seed_database()
