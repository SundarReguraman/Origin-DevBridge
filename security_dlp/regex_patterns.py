"""
Origin DevBridge - Security DLP Regex Signatures
================================================
Deterministic and high-entropy heuristic signatures for detecting
inadvertently exposed developer secrets, keys, and tokens.
"""

import re
from typing import Dict, Pattern

# Compiled high-precision token signatures
TOKEN_PATTERNS: Dict[str, Pattern[str]] = {
    "OPENAI_API_KEY": re.compile(
        r"(?:sk-[a-zA-Z0-9_-]{20,T[a-zA-Z0-9_-]{20,}|sk-proj-[a-zA-Z0-9_-]{48,})"
    ),
    "GITHUB_TOKEN": re.compile(
        r"(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,}"
    ),
    "AWS_ACCESS_KEY": re.compile(
        r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"
    ),
    "GENERIC_SECRET_KEY": re.compile(
        r'(?i)(?:api[_-]?key|secret[_-]?key|token|auth[_-]?token|passwd|password)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.\$\/]{16,})["\']?'
    ),
    "JWT_BEARER_TOKEN": re.compile(
        r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"
    ),
    "GENERIC_BEARER_HEADER": re.compile(
        r"(?i)bearer\s+([a-zA-Z0-9_\-\.]{24,})"
    ),
}