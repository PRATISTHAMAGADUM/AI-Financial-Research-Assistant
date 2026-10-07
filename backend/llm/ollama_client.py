import logging
import json
import requests
from typing import Dict, Any, Optional
from backend.config import settings

logger = logging.getLogger(__name__)

FINANCIAL_SYSTEM_PROMPT = """You are a precise, professional AI Financial Analyst assistant.
Your job is to answer financial questions accurately based STRICTLY on the provided retrieved financial context.

STRICT RULES TO FOLLOW:
1. Answer using ONLY facts, numbers, and statements explicitly present in the provided RETRIEVED CONTEXT.
2. NEVER invent, extrapolate, or hallucinate financial numbers, revenue figures, dates, or company facts.
3. If the retrieved context does NOT contain enough information to answer the question, state EXACTLY:
   "Insufficient information was found in the available financial sources."
4. Clearly distinguish direct reported facts from step-by-step mathematical calculations (such as YoY percentage change).
5. Always cite the company name, fiscal year, and source document when stating financial figures.
6. Keep explanations clear, professional, concise, and easy to understand for finance students and investors.
"""

class OllamaLLMClient:
    """Client for communicating with Phi-3 model hosted on local Ollama service."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
        self.timeout = settings.LLM_TIMEOUT

    def is_available(self) -> bool:
        """Check if local Ollama server is running and accessible."""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return res.status_code == 200
        except Exception:
            return False

    def check_health(self) -> bool:
        """Alias for is_available() health check."""
        return self.is_available()

    def generate_answer(self, prompt: str, context: str) -> str:
        """
        Generate a financial answer using Phi-3 via Ollama.
        If Ollama is unreachable, falls back to deterministic context synthesis.
        """
        full_prompt = f"RETRIEVED FINANCIAL CONTEXT:\n{context}\n\nUSER QUESTION: {prompt}\n\nANSWER:"

        if self.is_available():
            try:
                payload = {
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "system": FINANCIAL_SYSTEM_PROMPT,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature
                    }
                }
                logger.info(f"Sending request to Ollama endpoint ({self.model_name})...")
                res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data.get("response", "").strip()
                    if response_text:
                        return response_text
            except Exception as e:
                logger.warning(f"Ollama generation failed or timed out: {e}")

        # Deterministic Grounded Synthesis Fallback when Ollama offline
        logger.info("Using local fallback synthesis engine (Ollama offline)...")
        return self._fallback_synthesis(prompt, context)

    def _fallback_synthesis(self, prompt: str, context: str) -> str:
        """Fallback synthesis engine guaranteeing strictly grounded responses and general financial knowledge guidance."""
        prompt_lower = prompt.lower()

        # General financial knowledge topics (budgeting, investing, financial statements, ratios)
        if any(w in prompt_lower for w in ["budget", "budgeting", "save money", "saving"]):
            return (
                "### 💡 Why You Should Use a Budget (Financial Principle):\n\n"
                "A **budget** is a foundational financial plan that tracks income, controls spending, and aligns resource allocation with long-term goals. Here are key reasons to maintain a budget:\n\n"
                "1. **Cash Flow Control & Visibility:** Gives full transparency into fixed vs. variable expenses, preventing living paycheck-to-paycheck.\n"
                "2. **Emergency Fund & Debt Reduction:** Ensures a portion of income is automatically set aside for unexpected expenses (typically 3-6 months) and debt repayment.\n"
                "3. **Capital Allocation Discipline:** Just like corporate financial planning, personal budgeting enforces disciplined spending using rules like the **50/30/20 Rule** (50% Needs, 30% Wants, 20% Savings/Investments).\n"
                "4. **Wealth Compounding:** Frees up surplus capital to invest in income-generating assets (stocks, index funds, real estate).\n"
                "5. **Goal Achievement:** Helps measure progress toward major financial milestones such as purchasing a home, retirement, or business ventures."
            )

        if any(w in prompt_lower for w in ["diversif", "portfolio", "asset allocation", "investing"]):
            return (
                "### 📈 Principles of Investing & Portfolio Diversification:\n\n"
                "**Diversification** is a risk-management strategy that mixes a variety of investments within a portfolio:\n\n"
                "1. **Risk Reduction:** Spreading capital across equities, fixed income, real estate, and cash mitigates downside risk from individual asset failures.\n"
                "2. **Uncorrelated Returns:** Different asset classes perform differently under varying economic conditions (inflation, interest rate changes).\n"
                "3. **Compound Growth:** Long-term disciplined investing harnesses compounding interest to grow purchasing power over inflation."
            )

        if any(w in prompt_lower for w in ["balance sheet", "income statement", "cash flow statement", "financial statement"]):
            return (
                "### 📑 Core Financial Statements Overview:\n\n"
                "1. **Income Statement:** Reports Revenue, Operating Expenses, Operating Income, and Net Income over a period.\n"
                "2. **Balance Sheet:** Displays Assets, Liabilities, and Shareholders' Equity at a specific point in time (Assets = Liabilities + Equity).\n"
                "3. **Cash Flow Statement:** Shows Cash inflows and outflows from Operating, Investing, and Financing activities."
            )

        if not context or "Insufficient" in context:
            return "Insufficient information was found in the available corporate financial sources for this specific company query. Try asking about reported revenue, net income, cash flow, EPS, or general financial principles."

        lines = [line.strip() for line in context.split("\n") if line.strip()]
        relevant_lines = []
        for line in lines:
            if any(term in line.lower() for term in ["revenue:", "net income:", "eps:", "growth:", "risk", "financial performance"]):
                relevant_lines.append(line)

        if not relevant_lines:
            relevant_lines = lines[:5]

        synthesis = f"Based strictly on retrieved financial records:\n\n"
        synthesis += "\n".join([f"• {line}" for line in relevant_lines[:6]])
        synthesis += "\n\n(Note: Generated via fallback engine. Start Ollama with 'ollama run phi3' for live Phi-3 model responses.)"
        return synthesis

ollama_client = OllamaLLMClient()
