from abc import ABC, abstractmethod
from typing import List, Optional
from backend.ingestion.models import FinancialReportDocument

class BaseFinancialProvider(ABC):
    """Abstract base interface for financial data providers."""

    @abstractmethod
    def get_company_overview(self, ticker: str) -> Optional[dict]:
        """Fetch general company profile and metadata."""
        pass

    @abstractmethod
    def fetch_financial_documents(self, ticker: str, years: List[int]) -> List[FinancialReportDocument]:
        """Fetch quarterly/annual financial documents and reports for a ticker."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass
