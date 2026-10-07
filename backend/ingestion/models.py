from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class FinancialMetrics(BaseModel):
    revenue: Optional[float] = Field(None, description="Total Revenue in USD")
    net_income: Optional[float] = Field(None, description="Net Income in USD")
    eps: Optional[float] = Field(None, description="Earnings Per Share in USD")
    operating_income: Optional[float] = Field(None, description="Operating Income in USD")
    total_assets: Optional[float] = Field(None, description="Total Assets in USD")
    total_liabilities: Optional[float] = Field(None, description="Total Liabilities in USD")
    operating_cash_flow: Optional[float] = Field(None, description="Operating Cash Flow in USD")
    revenue_growth: Optional[float] = Field(None, description="Revenue Growth Rate (%)")
    profit_growth: Optional[float] = Field(None, description="Net Income Profit Growth Rate (%)")
    profit_margin: Optional[float] = Field(None, description="Net Profit Margin (%)")

class FinancialReportDocument(BaseModel):
    company_name: str
    ticker: str
    industry: str
    year: int
    quarter: str = "Annual"
    document_type: str = "Financial Report"  # 10-K, 10-Q, Annual Report, Earnings Summary
    metrics: FinancialMetrics
    risk_factors: List[str] = Field(default_factory=list)
    financial_events: List[str] = Field(default_factory=list)
    text_content: str
    source_name: str
    source_url: str
    retrieval_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))

    def to_metadata(self) -> Dict[str, Any]:
        """Convert key attributes to ChromaDB compatible flat metadata dict."""
        return {
            "company": self.company_name,
            "ticker": self.ticker.upper(),
            "year": int(self.year),
            "quarter": self.quarter,
            "document_type": self.document_type,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "retrieval_date": self.retrieval_date,
            "industry": self.industry
        }
