"""
Origin DevBridge - Security DLP In-Memory Sanitizer
===================================================
Executes zero-retention in-memory redaction and volatile buffer clearing.
"""

from dataclasses import dataclass, field
from typing import List, Tuple
import ctypes
from .regex_patterns import TOKEN_PATTERNS


@dataclass
class RedactionAudit:
    pattern_name: str
    redacted_count: int
    matched_previews: List[str] = field(default_factory=list)


class SecuritySanitizer:
    def __init__(self, mask_placeholder: str = "[REDACTED_SECRET]"):
        self.mask = mask_placeholder

    def sanitize_text(self, raw_text: str) -> Tuple[str, List[RedactionAudit]]:
        """
        Scans and redacts detected secrets within the provided text.
        Returns:
            (sanitized_text, list_of_audit_records)
        """
        cleaned = raw_text
        audit_records: List[RedactionAudit] = []

        for name, pattern in TOKEN_PATTERNS.items():
            matches = list(pattern.finditer(cleaned))
            if not matches:
                continue

            previews = []
            for m in matches:
                matched_str = m.group(0)
                # Obfuscated preview for audit logs (e.g. sk-pro...9a2f)
                if len(matched_str) > 8:
                    preview = f"{matched_str[:4]}...{matched_str[-4:]}"
                else:
                    preview = "****"
                previews.append(preview)

            # Perform redaction substitution
            cleaned = pattern.sub(self.mask, cleaned)

            audit_records.append(
                RedactionAudit(
                    pattern_name=name,
                    redacted_count=len(matches),
                    matched_previews=previews,
                )
            )

        return cleaned, audit_records

    @staticmethod
    def zero_wipe_buffer(buffer: bytearray) -> None:
        """
        Overwrites volatile memory buffer with zeroes to prevent forensic remanence.
        """
        if not isinstance(buffer, (bytearray, memoryview)):
            return
        ctypes.memset((ctypes.c_char * len(buffer)).from_buffer(buffer), 0, len(buffer))


# -------------------------------------------------------------
# Standalone CLI Verification Test
# -------------------------------------------------------------
if __name__ == "__main__":
    sanitizer = SecuritySanitizer()

    dirty_sample = (
        "Client App -> Gateway [auth: sk-proj-9x7K18aBcDeFgHiJkLmNoPqRsTuVwXyZ01234567890] "
        "-> Postgres DB [aws_key: AKIAIOSFODNN7EXAMPLE]"
    )

    print("\n[ORIGINAL INPUT]")
    print(dirty_sample)

    cleaned_text, audits = sanitizer.sanitize_text(dirty_sample)

    print("\n[SANITIZED OUTPUT]")
    print(cleaned_text)

    print("\n[SECURITY AUDIT LOGS]")
    for record in audits:
        print(f"  • {record.pattern_name}: {record.redacted_count} occurrence(s) masked {record.matched_previews}")
    print()