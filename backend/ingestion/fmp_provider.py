import logging
import requests
from typing import List, Optional, Dict, Any
from backend.config import settings
from backend.ingestion.base_provider import BaseFinancialProvider
from backend.ingestion.models import FinancialReportDocument, FinancialMetrics

logger = logging.getLogger(__name__)

class FinancialModelingPrepProvider(BaseFinancialProvider):
    """Financial Modeling Prep (FMP) API provider implementation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.FMP_API_KEY
        self.base_url = "https://financialmodelingprep.com/api/v3"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip() != "")

    def get_company_overview(self, ticker: str) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None
        url = f"{self.base_url}/profile/{ticker.upper()}?apikey={self.api_key}"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
        except Exception as e:
            logger.warning(f"FMP get_company_overview failed for {ticker}: {e}")
        return None

    def fetch_financial_documents(self, ticker: str, years: List[int]) -> List[FinancialReportDocument]:
        if not self.is_available():
            return []
        documents = []
        try:
            url = f"{self.base_url}/income-statement/{ticker.upper()}?limit=10&apikey={self.api_key}"
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                return []
            statements = res.json()
            if not isinstance(statements, list):
                return []

            profile = self.get_company_overview(ticker)
            company_name = profile.get("companyName", ticker.upper()) if profile else ticker.upper()
            industry = profile.get("industry", "Technology") if profile else "General"

            for stmt in statements:
                date_str = stmt.get("date", "")
                if not date_str:
                    continue
                year = int(date_str.split("-")[0])
                if year not in years:
                    continue

                rev = float(stmt.get("revenue", 0) or 0)
                net_inc = float(stmt.get("netIncome", 0) or 0)
                op_inc = float(stmt.get("operatingIncome", 0) or 0)
                eps_val = float(stmt.get("eps", 0) or 0)

                metrics = FinancialMetrics(
                    revenue=rev if rev > 0 else None,
                    net_income=net_inc,
                    operating_income=op_inc,
                    eps=eps_val if eps_val else None,
                    profit_margin=(net_inc / rev * 100) if rev else None
                )

                content = (
                    f"Financial Statement for {company_name} ({ticker.upper()}) Year {year}.\n"
                    f"Revenue: ${rev:,.2f}, Net Income: ${net_inc:,.2f}, Operating Income: ${op_inc:,.2f}, EPS: ${eps_val:.2f}.\n"
                    f"Source: Financial Modeling Prep API."
                )

                doc = FinancialReportDocument(
                    company_name=company_name,
                    ticker=ticker.upper(),
                    industry=industry,
                    year=year,
                    quarter="Annual",
                    document_type="Income Statement",
                    metrics=metrics,
                    text_content=content,
                    source_name="Financial Modeling Prep API",
                    source_url=f"https://financialmodelingprep.com/api/v3/income-statement/{ticker.upper()}"
                )
                documents.append(doc)
        except Exception as e:
            logger.error(f"FMP fetch_financial_documents failed for {ticker}: {e}")
        return documents
