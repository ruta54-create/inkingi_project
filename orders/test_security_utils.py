# orders/test_security_utils.py
"""
Tests for security utilities, especially header redaction.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from .security_utils import (
    is_sensitive_header, 
    redact_header_value, 
    redact_headers,
    redact_request_headers,
    safe_json_dump
)

User = get_user_model()

class HeaderRedactionTests(TestCase):
    """Test header redaction security functionality."""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    def test_sensitive_header_detection(self):
        """Test that sensitive headers are correctly identified."""
        # Should be detected as sensitive
        sensitive_headers = [
            'HTTP_AUTHORIZATION',
            'HTTP_STRIPE_SIGNATURE', 
            'HTTP_X_API_KEY',
            'HTTP_BEARER_TOKEN',
            'HTTP_WEBHOOK_SECRET',
            'HTTP_PAYMENT_TOKEN',
            'HTTP_SESSION_ID',
            'HTTP_COOKIE'
        ]
        
        for header in sensitive_headers:
            with self.subTest(header=header):
                self.assertTrue(is_sensitive_header(header), 
                              f"Header {header} should be detected as sensitive")
    
    def test_non_sensitive_header_detection(self):
        """Test that non-sensitive headers are not flagged."""
        non_sensitive_headers = [
            'HTTP_USER_AGENT',
            'HTTP_ACCEPT',
            'HTTP_CONTENT_TYPE',
            'HTTP_HOST',
            'HTTP_REFERER'
        ]
        
        for header in non_sensitive_headers:
            with self.subTest(header=header):
                self.assertFalse(is_sensitive_header(header),
                               f"Header {header} should not be detected as sensitive")
    
    def test_header_value_redaction_short(self):
        """Test redaction of short sensitive values."""
        short_value = "abc123"
        redacted = redact_header_value(short_value)
        self.assertEqual(redacted, "****")
    
    def test_header_value_redaction_medium(self):
        """Test redaction of medium-length sensitive values."""
        medium_value = "bearer_token_12345"
        redacted = redact_header_value(medium_value)
        self.assertTrue(redacted.startswith("be"))
        self.assertTrue(redacted.endswith("45"))
        self.assertIn("...", redacted)
    
    def test_header_value_redaction_long(self):
        """Test redaction of very long sensitive values."""
        long_value = "x" * 150  # 150 character string
        redacted = redact_header_value(long_value)
        self.assertTrue(redacted.startswith("[REDACTED-"))
        self.assertIn("150chars]", redacted)
    
    def test_headers_dictionary_redaction(self):
        """Test redaction of a headers dictionary."""
        headers = {
            'HTTP_AUTHORIZATION': 'Bearer secret_token_123',
            'HTTP_USER_AGENT': 'Mozilla/5.0 (compatible)',
            'HTTP_STRIPE_SIGNATURE': 'stripe_signature_value',
            'HTTP_CONTENT_TYPE': 'application/json'
        }
        
        redacted = redact_headers(headers)
        
        # Sensitive headers should be redacted
        self.assertNotEqual(redacted['HTTP_AUTHORIZATION'], headers['HTTP_AUTHORIZATION'])
        self.assertNotEqual(redacted['HTTP_STRIPE_SIGNATURE'], headers['HTTP_STRIPE_SIGNATURE'])
        
        # Non-sensitive headers should remain unchanged
        self.assertEqual(redacted['HTTP_USER_AGENT'], headers['HTTP_USER_AGENT'])
        self.assertEqual(redacted['HTTP_CONTENT_TYPE'], headers['HTTP_CONTENT_TYPE'])
    
    def test_request_header_redaction(self):
        """Test redaction of headers from Django request object."""
        request = self.factory.post('/webhook/', 
                                  HTTP_AUTHORIZATION='Bearer secret123',
                                  HTTP_USER_AGENT='TestAgent/1.0',
                                  HTTP_STRIPE_SIGNATURE='stripe_sig_value')
        
        redacted = redact_request_headers(request)
        
        # Should have HTTP_ prefixed headers
        self.assertIn('HTTP_AUTHORIZATION', redacted)
        self.assertIn('HTTP_USER_AGENT', redacted)
        self.assertIn('HTTP_STRIPE_SIGNATURE', redacted)
        
        # Sensitive headers should be redacted
        self.assertNotEqual(redacted['HTTP_AUTHORIZATION'], 'Bearer secret123')
        self.assertNotEqual(redacted['HTTP_STRIPE_SIGNATURE'], 'stripe_sig_value')
        
        # Non-sensitive should remain
        self.assertEqual(redacted['HTTP_USER_AGENT'], 'TestAgent/1.0')
    
    def test_safe_json_dump(self):
        """Test safe JSON serialization."""
        data = {'key': 'value', 'number': 123}
        result = safe_json_dump(data)
        self.assertIn('key', result)
        self.assertIn('value', result)
    
    def test_empty_and_none_values(self):
        """Test handling of empty and None values."""
        self.assertFalse(is_sensitive_header(''))
        self.assertFalse(is_sensitive_header(None))
        
        self.assertEqual(redact_header_value(''), '')
        self.assertEqual(redact_header_value(None), '')
        
        self.assertEqual(redact_headers({}), {})
        self.assertEqual(redact_headers(None), {})
    
    def test_case_insensitive_detection(self):
        """Test that header detection is case insensitive."""
        headers = [
            'http_authorization',
            'HTTP_AUTHORIZATION', 
            'Http_Authorization',
            'HTTP_stripe_signature'
        ]
        
        for header in headers:
            with self.subTest(header=header):
                self.assertTrue(is_sensitive_header(header))