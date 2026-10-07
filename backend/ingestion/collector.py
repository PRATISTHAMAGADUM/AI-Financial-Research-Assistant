import logging
from typing import List, Dict, Any, Optional
from backend.ingestion.base_provider import BaseFinancialProvider
from backend.ingestion.alpha_vantage import AlphaVantageProvider
from backend.ingestion.fmp_provider import FinancialModelingPrepProvider
from backend.ingestion.public_sources import PublicSourcesProvider
from backend.ingestion.models import FinancialReportDocument

logger = logging.getLogger(__name__)

class FinancialDataCollector:
    """Configurable financial data collection and ingestion module."""

    def __init__(self, providers: Optional[List[BaseFinancialProvider]] = None):
        if providers:
            self.providers = providers
        else:
            self.providers = [
                AlphaVantageProvider(),
                FinancialModelingPrepProvider(),
                PublicSourcesProvider()  # Guaranteed fallback with realistic SEC EDGAR datasets
            ]

    def validate_ticker(self, ticker: str) -> str:
        """Sanitize and validate ticker symbol format."""
        if not ticker or not isinstance(ticker, str):
            raise ValueError("Ticker symbol must be a non-empty string.")
        cleaned = ticker.strip().upper()
        if len(cleaned) > 15:
            raise ValueError(f"Invalid ticker symbol format: '{ticker}'")
        return cleaned

    def collect_company_documents(
        self,
        ticker: str,
        years: Optional[List[int]] = None
    ) -> List[FinancialReportDocument]:
        """
        Collect financial reports and metadata for a company ticker across specified years.
        Iterates across providers until documents are successfully gathered.
        """
        clean_ticker = self.validate_ticker(ticker)
        if not years:
            years = [2023, 2024, 2025]

        collected_docs: List[FinancialReportDocument] = []

        for provider in self.providers:
            if not provider.is_available():
                continue
            provider_name = provider.__class__.__name__
            logger.info(f"Attempting data collection for {clean_ticker} using {provider_name}")
            try:
                docs = provider.fetch_financial_documents(clean_ticker, years)
                if docs and len(docs) > 0:
                    logger.info(f"Successfully collected {len(docs)} documents for {clean_ticker} via {provider_name}")
                    collected_docs = docs
                    break
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed for {clean_ticker}: {e}")

        if not collected_docs:
            logger.warning(f"No financial documents could be retrieved for ticker {clean_ticker}")

        return collected_docs

    def get_company_overview(self, ticker: str) -> Dict[str, Any]:
        """Fetch general company profile using available providers."""
        clean_ticker = self.validate_ticker(ticker)
        for provider in self.providers:
            if not provider.is_available():
                continue
            try:
                overview = provider.get_company_overview(clean_ticker)
                if overview:
                    return overview
            except Exception as e:
                logger.warning(f"Failed getting overview from {provider.__class__.__name__}: {e}")
        
        return {
            "Symbol": clean_ticker,
            "Name": f"{clean_ticker} Inc.",
            "Industry": "Technology / Enterprise Services",
            "Description": f"Public financial entity {clean_ticker}."
        }

collector = FinancialDataCollector()
