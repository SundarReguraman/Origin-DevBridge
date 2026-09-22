from security_dlp.sanitizer import SecuritySanitizer


def test_openai_key_redaction():
  sanitizer = SecuritySanitizer()
  dirty_text = (
      "Service Node: auth-service"
      " [sk-proj-abc12345678901234567890123456789012345678901234567890]"
  )
  cleaned, audits = sanitizer.sanitize_text(dirty_text)

  assert "[REDACTED_SECRET]" in cleaned
  assert "sk-proj-" not in cleaned
  assert len(audits) == 1
  assert audits[0].pattern_name == "OPENAI_API_KEY"


def test_aws_key_redaction():
  sanitizer = SecuritySanitizer()
  dirty_text = "DB Node [key: AKIAIOSFODNN7EXAMPLE]"
  cleaned, audits = sanitizer.sanitize_text(dirty_text)

  assert "[REDACTED_SECRET]" in cleaned
  assert "AKIAIOSFODNN7EXAMPLE" not in cleaned
  assert audits[0].pattern_name == "AWS_ACCESS_KEY"


def test_clean_text_untouched():
  sanitizer = SecuritySanitizer()
  clean_text = "FastAPI -> Redis Cache -> PostgreSQL DB"
  cleaned, audits = sanitizer.sanitize_text(clean_text)

  assert cleaned == clean_text
  assert len(audits) == 0