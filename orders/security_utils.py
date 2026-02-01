# orders/security_utils.py
"""
Security utilities for header redaction and sensitive data handling.
"""
import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Comprehensive list of sensitive header patterns
SENSITIVE_HEADER_PATTERNS = [
    'auth', 'authorization', 'token', 'key', 'secret', 'password', 
    'credential', 'session', 'cookie', 'signature', 'bearer',
    'api_key', 'apikey', 'access_token', 'refresh_token', 'jwt',
    'stripe', 'payment', 'billing', 'card', 'account', 'client_secret',
    'webhook_secret', 'private', 'confidential', 'internal'
]

def is_sensitive_header(header_name: str) -> bool:
    """
    Check if header contains sensitive information based on comprehensive patterns.
    
    Args:
        header_name: The header name to check
        
    Returns:
        bool: True if header is considered sensitive
    """
    if not header_name:
        return False
        
    name_lower = header_name.lower()
    return any(pattern in name_lower for pattern in SENSITIVE_HEADER_PATTERNS)

def redact_header_value(value: Any, header_name: str = "") -> str:
    """
    Securely redact header values with appropriate masking strategy.
    
    Args:
        value: The header value to redact
        header_name: Optional header name for context
        
    Returns:
        str: Redacted value
    """
    if not value:
        return str(value) if value is not None else ""
    
    str_value = str(value)
    
    # For very long values, show only length for security
    if len(str_value) > 100:
        return f"[REDACTED-{len(str_value)}chars]"
    
    # For shorter sensitive values, show partial info for debugging
    if len(str_value) <= 8:
        return "****"
    else:
        # Show first 2 and last 2 chars while maintaining security
        return f"{str_value[:2]}...{str_value[-2:]}"

def redact_headers(headers: Dict[str, Any], max_non_sensitive_length: int = 200) -> Dict[str, Any]:
    """
    Apply comprehensive header redaction with security logging.
    
    Args:
        headers: Dictionary of headers to redact
        max_non_sensitive_length: Maximum length for non-sensitive headers
        
    Returns:
        Dict[str, Any]: Dictionary with redacted headers
    """
    if not headers:
        return {}
    
    masked = {}
    sensitive_headers_found = []
    
    for header_name, header_value in headers.items():
        if is_sensitive_header(header_name):
            masked[header_name] = redact_header_value(header_value, header_name)
            sensitive_headers_found.append(header_name)
        else:
            # Still limit non-sensitive headers to prevent log bloat
            str_value = str(header_value)
            if len(str_value) > max_non_sensitive_length:
                masked[header_name] = str_value[:max_non_sensitive_length] + "..."
            else:
                masked[header_name] = header_value
    
    # Security audit logging
    if sensitive_headers_found:
        # Limit logged header names to prevent log spam
        logged_headers = sensitive_headers_found[:5]
        header_list = ', '.join(logged_headers)
        if len(sensitive_headers_found) > 5:
            header_list += f" (and {len(sensitive_headers_found) - 5} more)"
            
        logger.warning(
            f"Redacted {len(sensitive_headers_found)} sensitive headers: {header_list}",
            extra={
                'sensitive_header_count': len(sensitive_headers_found),
                'redacted_headers': sensitive_headers_found[:10]  # Limit for security
            }
        )
    
    return masked

def redact_request_headers(request) -> Dict[str, Any]:
    """
    Extract and redact HTTP headers from Django request object.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        Dict[str, Any]: Redacted headers dictionary
    """
    # Extract HTTP headers from request.META
    headers = {k: v for k, v in request.META.items() if k.startswith('HTTP_')}
    
    return redact_headers(headers)

def safe_json_dump(data: Dict[str, Any]) -> str:
    """
    Safely serialize dictionary to JSON with error handling.
    
    Args:
        data: Dictionary to serialize
        
    Returns:
        str: JSON string or error message
    """
    try:
        return json.dumps(data, default=str, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize data to JSON: {e}")
        return f"[JSON_SERIALIZATION_ERROR: {str(e)}]"

# Additional security patterns for specific use cases
PAYMENT_SENSITIVE_PATTERNS = [
    'stripe', 'paypal', 'square', 'braintree', 'razorpay',
    'payment', 'billing', 'card', 'cvv', 'expiry'
]

def is_payment_sensitive(header_name: str) -> bool:
    """Check if header is payment-related and sensitive."""
    if not header_name:
        return False
    name_lower = header_name.lower()
    return any(pattern in name_lower for pattern in PAYMENT_SENSITIVE_PATTERNS)