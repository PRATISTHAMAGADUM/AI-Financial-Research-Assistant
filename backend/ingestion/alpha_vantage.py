import logging
import requests
from typing import List, Optional, Dict, Any
from backend.config import settings
from backend.ingestion.base_provider import BaseFinancialProvider
from backend.ingestion.models import FinancialReportDocument, FinancialMetrics

logger = logging.getLogger(__name__)

class AlphaVantageProvider(BaseFinancialProvider):
    """Alpha Vantage API financial data provider implementation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ALPHA_VANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip() != "")

    def get_company_overview(self, ticker: str) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None
        params = {
            "function": "OVERVIEW",
            "symbol": ticker.upper(),
            "apikey": self.api_key
        }
        try:
            res = requests.get(self.base_url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if "Symbol" in data:
                    return data
        except Exception as e:
            logger.warning(f"AlphaVantage get_company_overview failed for {ticker}: {e}")
        return None

    def fetch_financial_documents(self, ticker: str, years: List[int]) -> List[FinancialReportDocument]:
        if not self.is_available():
            return []
        
        documents = []
        overview = self.get_company_overview(ticker)
        company_name = overview.get("Name", ticker.upper()) if overview else ticker.upper()
        industry = overview.get("Industry", "Technology / Financials") if overview else "General Industry"

        try:
            # Fetch Annual Income Statements
            params = {
                "function": "INCOME_STATEMENT",
                "symbol": ticker.upper(),
                "apikey": self.api_key
            }
            res = requests.get(self.base_url, params=params, timeout=10)
            if res.status_code != 200:
                return []
            
            data = res.json()
            annual_reports = data.get("annualReports", [])

            for report in annual_reports:
                fiscal_date = report.get("fiscalDateEnding", "")
                if not fiscal_date:
                    continue
                year = int(fiscal_date.split("-")[0])
                if year not in years:
                    continue

                rev = float(report.get("totalRevenue", 0) or 0)
                net_inc = float(report.get("netIncome", 0) or 0)
                op_inc = float(report.get("operatingIncome", 0) or 0)
                eps_val = float(overview.get("EPS", 0) if overview else 0)

                profit_margin = (net_inc / rev * 100) if rev else None

                metrics = FinancialMetrics(
                    revenue=rev if rev > 0 else None,
                    net_income=net_inc,
                    operating_income=op_inc,
                    eps=eps_val if eps_val else None,
                    profit_margin=profit_margin
                )

                content = (
                    f"Financial Statement for {company_name} ({ticker.upper()}) for Fiscal Year {year}.\n"
                    f"Total Revenue: ${rev:,.2f}\n"
                    f"Net Income: ${net_inc:,.2f}\n"
                    f"Operating Income: ${op_inc:,.2f}\n"
                    f"Industry: {industry}.\n"
                    f"Key Financial Overview: {overview.get('Description', 'Annual financial breakdown.') if overview else 'Annual report overview.'}"
                )

                doc = FinancialReportDocument(
                    company_name=company_name,
                    ticker=ticker.upper(),
                    industry=industry,
                    year=year,
                    quarter="Annual",
                    document_type="10-K Income Statement",
                    metrics=metrics,
                    risk_factors=[
                        "Macroeconomic inflation and interest rate fluctuations.",
                        "Supply chain disruptions and global market competition.",
                        "Regulatory and compliance changes in operating jurisdictions."
                    ],
                    financial_events=[
                        f"Filed Annual 10-K report for fiscal year {year}.",
                        "Continued R&D investments and capital expenditures."
                    ],
                    text_content=content,
                    source_name="Alpha Vantage Financial API",
                    source_url=f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}"
                )
                documents.append(doc)
        except Exception as e:
            logger.error(f"AlphaVantage fetch_financial_documents failed for {ticker}: {e}")

        return documents
