"""
Domain Validator agent (Section 2 of spec).

Performs a *semantic* check of whether a research question is
substantially related to Computer Science & Engineering, rather than a
keyword match. Implemented as its own module so it can later be promoted
to a standalone agent process without changing its call signature.
"""
from __future__ import annotations

from app.models.schemas import DomainValidationResult
from app.services.llm_client import LLMError, get_llm_client

SYSTEM_PROMPT = """You are the Domain Validator agent inside an Agentic CSE \
Research Assistant. Your only job is to decide whether a user's research \
question is substantially related to Computer Science and Engineering \
(CSE), using semantic understanding rather than keyword matching.

CSE includes (non-exhaustively): AI/ML/DL, NLP, computer vision, generative \
and agentic AI, reinforcement learning, data science, algorithms and data \
structures, distributed systems, operating systems, computer networks, \
databases, software engineering, cybersecurity, cryptography, cloud/edge \
computing, IoT, HCI, information retrieval, computer architecture, \
compilers, programming languages, robotics, quantum computing, HPC, \
recommender systems, computer graphics, and computationally-framed \
bioinformatics.

A question can be CSE-related even if it also touches another field \
(e.g. "using ML to predict protein folding" is CSE + biology). Reject \
only questions with no substantial CSE angle (e.g. pure biology, pure \
finance, general history, unrelated humanities).

Respond with ONLY a JSON object, no prose, no markdown fences, matching \
exactly this shape:
{
  "is_cse_related": boolean,
  "domain": string or null,          // e.g. "Machine Learning"
  "subdomain": string or null,       // e.g. "Federated Learning"
  "confidence": number,              // 0.0-1.0
  "rationale": string,               // 1-3 sentences, shown to the user
  "suggested_reformulation": string or null  // only if rejected: how the
                                              // user could reframe toward CSE,
                                              // or null if no clear CSE angle
}"""


async def validate_domain(research_question: str) -> DomainValidationResult:
    """Returns a DomainValidationResult. Raises LLMError on transport/parse
    failure; the caller is responsible for recording that as a failed stage
    (Section 22) rather than treating it as an implicit rejection."""
    client = get_llm_client()
    user_prompt = f'Research question to evaluate:\n"""\n{research_question}\n"""'

    try:
        raw = await client.complete_json(SYSTEM_PROMPT, user_prompt, max_tokens=512)
        return DomainValidationResult(**raw)
    except (LLMError, TypeError, ValueError) as exc:
        raise LLMError(f"Domain validation failed: {exc}") from exc
