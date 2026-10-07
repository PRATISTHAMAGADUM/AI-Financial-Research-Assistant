import re
import logging
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
from backend.config import settings

logger = logging.getLogger(__name__)

class GroundingClaimResult(Dict[str, Any]):
    claim: str
    supported: bool
    evidence_snippet: str

class GroundingVerificationResult:
    def __init__(
        self,
        grounding_score: float,
        is_grounded: bool,
        claims: List[Dict[str, Any]],
        warning_message: str = ""
    ):
        self.grounding_score = grounding_score  # Float between 0.0 and 1.0 (e.g. 0.92 = 92%)
        self.grounding_percentage = round(grounding_score * 100, 1)
        self.is_grounded = is_grounded
        self.claims = claims
        self.warning_message = warning_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "grounding_score": self.grounding_score,
            "grounding_percentage": self.grounding_percentage,
            "is_grounded": self.is_grounded,
            "claims": self.claims,
            "warning_message": self.warning_message
        }

class GroundingVerifier:
    """Verifies that generated LLM responses are grounded in retrieved evidence."""

    def __init__(self, threshold: float = None):
        self.threshold = threshold if threshold is not None else settings.GROUNDING_THRESHOLD

    def _extract_claims(self, text: str) -> List[str]:
        """Extract atomic claim sentences from answer text."""
        if not text or "Insufficient information" in text:
            return []

        # Split into sentences
        raw_sentences = re.split(r'(?<=[.!?])\s+', text)
        claims = []
        for s in raw_sentences:
            s_clean = s.strip()
            # Ignore structural header lines or fallback notes
            if not s_clean or s_clean.startswith("(Note:") or s_clean.startswith("Based strictly"):
                continue
            if len(s_clean) > 10:
                claims.append(s_clean)
        return claims

    def verify_answer(self, answer: str, context_docs: List[Document]) -> GroundingVerificationResult:
        """
        Verify claims in LLM answer against retrieved context documents.
        Computes grounding score and claim verification breakdown.
        """
        if "Insufficient information was found" in answer:
            return GroundingVerificationResult(
                grounding_score=1.0,
                is_grounded=True,
                claims=[{
                    "claim": "Insufficient information response.",
                    "supported": True,
                    "evidence_snippet": "System correctly refused to fabricate unverified data."
                }],
                warning_message=""
            )

        context_combined = "\n".join([doc.page_content for doc in context_docs]).lower()
        claims_text = self._extract_claims(answer)

        if not claims_text:
            return GroundingVerificationResult(
                grounding_score=1.0,
                is_grounded=True,
                claims=[],
                warning_message=""
            )

        verified_claims: List[Dict[str, Any]] = []
        supported_count = 0

        for claim in claims_text:
            is_sup, snippet = self._verify_single_claim(claim, context_docs, context_combined)
            if is_sup:
                supported_count += 1

            verified_claims.append({
                "claim": claim,
                "supported": is_sup,
                "evidence_snippet": snippet
            })

        score = supported_count / len(claims_text) if claims_text else 1.0
        is_grounded = score >= self.threshold

        warning = ""
        if not is_grounded:
            warning = f"⚠️ Grounding score ({round(score*100, 1)}%) is below threshold ({round(self.threshold*100, 1)}%). This answer may contain unsupported information."

        return GroundingVerificationResult(
            grounding_score=score,
            is_grounded=is_grounded,
            claims=verified_claims,
            warning_message=warning
        )

    def _verify_single_claim(self, claim: str, context_docs: List[Document], context_combined: str) -> Tuple[bool, str]:
        """Check if a claim's numeric figures or key tokens are supported by context."""
        claim_lower = claim.lower()

        # 1. Check numbers present in claim
        numbers_in_claim = re.findall(r'\$?\d+(?:\.\d+)?%?', claim)

        # Find best matching context doc
        matching_snippet = "No direct context match found."
        matched = False

        for doc in context_docs:
            doc_text = doc.page_content.lower()
            if numbers_in_claim:
                num_matches = [num.lower().replace("$", "").replace("%", "").replace(",", "") for num in numbers_in_claim]
                # Filter out pure 4-digit year numbers if there are other financial amounts
                financial_nums = [n for n in num_matches if not (len(n) == 4 and n.startswith("20"))]
                nums_to_check = financial_nums if financial_nums else num_matches

                # ALL numeric figures in the claim must be present in the retrieved doc
                all_matched = True
                for nm in nums_to_check:
                    pattern = rf'\b{re.escape(nm)}\b'
                    if not re.search(pattern, doc_text):
                        all_matched = False
                        break
                
                if all_matched:
                    matched = True
                    matching_snippet = doc.page_content[:180] + "..."
                    break
            else:
                # Token overlap check for non-numeric claims
                words = [w for w in claim_lower.split() if len(w) > 4 and w not in ["about", "company", "which", "there", "their"]]
                if words:
                    matched_words = [w for w in words if re.search(rf'\b{re.escape(w)}\b', doc_text)]
                    if len(matched_words) >= min(2, len(words)):
                        matched = True
                        matching_snippet = doc.page_content[:180] + "..."
                        break

        return matched, matching_snippet

grounding_verifier = GroundingVerifier()
