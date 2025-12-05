import re
from typing import Optional
from src.config import SanitizationConfig

class Sanitizer:
    def __init__(self, config: SanitizationConfig):
        self.config = config
        # Simple regex patterns for demo purposes
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'

    def sanitize(self, text: str) -> str:
        """
        Redacts PII from the text if enabled in config.
        """
        if not self.config.redact_user_pii:
            return text

        redacted_text = text
        
        # Redact Emails
        redacted_text = re.sub(self.email_pattern, "[EMAIL REDACTED]", redacted_text)
        
        # Redact Phone Numbers (US format)
        redacted_text = re.sub(self.phone_pattern, "[PHONE REDACTED]", redacted_text)
        
        if redacted_text != text:
            print(f"🔒 PII Redacted from query.")
            
        return redacted_text

