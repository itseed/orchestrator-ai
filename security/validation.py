"""
Input Validation & Output Sanitization
Security validation and sanitization
"""

import re
import html
from typing import Any, Dict, List, Optional
from monitoring import get_logger

logger = get_logger(__name__)


class InputValidator:
    """Input validation for security"""
    
    def __init__(self):
        """Initialize input validator"""
        # Common dangerous patterns
        self.dangerous_patterns = [
            (r'<script.*?>.*?</script>', 'Script tags'),
            (r'javascript:', 'JavaScript protocol'),
            (r'on\w+\s*=', 'Event handlers'),
            (r'<iframe.*?>', 'IFrame tags'),
            (r'data:text/html', 'Data URLs'),
        ]
        
        logger.info("InputValidator initialized")
    
    def validate_string(
        self,
        value: str,
        max_length: Optional[int] = None,
        allowed_chars: Optional[str] = None,
        min_length: int = 0
    ) -> tuple[bool, Optional[str]]:
        """
        Validate string input
        
        Args:
            value: String to validate
            max_length: Maximum length
            allowed_chars: Optional regex pattern for allowed characters
            min_length: Minimum length
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, str):
            return False, "Value must be a string"
        
        if len(value) < min_length:
            return False, f"String must be at least {min_length} characters"
        
        if max_length and len(value) > max_length:
            return False, f"String must be at most {max_length} characters"
        
        # Check for dangerous patterns
        for pattern, description in self.dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                logger.warning("Dangerous pattern detected", pattern=description, value_preview=value[:50])
                return False, f"Dangerous pattern detected: {description}"
        
        # Check allowed characters
        if allowed_chars:
            if not re.match(allowed_chars, value):
                return False, "String contains invalid characters"
        
        return True, None
    
    def validate_dict(
        self,
        data: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate dictionary input
        
        Args:
            data: Dictionary to validate
            schema: Optional validation schema
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "Value must be a dictionary"
        
        if schema:
            # Validate required fields
            required = schema.get('required', [])
            for field in required:
                if field not in data:
                    return False, f"Required field missing: {field}"
            
            # Validate field types
            properties = schema.get('properties', {})
            for field, value in data.items():
                if field in properties:
                    field_schema = properties[field]
                    field_type = field_schema.get('type')
                    
                    if field_type == 'string':
                        valid, error = self.validate_string(
                            value,
                            max_length=field_schema.get('maxLength'),
                            min_length=field_schema.get('minLength', 0)
                        )
                        if not valid:
                            return False, f"Field '{field}': {error}"
        
        return True, None
    
    def sanitize_string(self, value: str) -> str:
        """Sanitize string by escaping HTML"""
        return html.escape(value)


class OutputSanitizer:
    """Output sanitization for security"""
    
    def __init__(self):
        """Initialize output sanitizer"""
        logger.info("OutputSanitizer initialized")
    
    def sanitize_output(self, data: Any) -> Any:
        """
        Sanitize output data
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized data
        """
        if isinstance(data, str):
            return html.escape(data)
        elif isinstance(data, dict):
            return {k: self.sanitize_output(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_output(item) for item in data]
        else:
            return data
    
    def remove_sensitive_data(
        self,
        data: Dict[str, Any],
        sensitive_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Remove sensitive data from output
        
        Args:
            data: Data dictionary
            sensitive_fields: List of sensitive field names
            
        Returns:
            Data with sensitive fields removed/masked
        """
        sensitive_fields = sensitive_fields or [
            'password', 'token', 'api_key', 'secret',
            'authorization', 'credentials', 'private_key'
        ]
        
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            is_sensitive = any(field in key_lower for field in sensitive_fields)
            
            if is_sensitive:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self.remove_sensitive_data(value, sensitive_fields)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.remove_sensitive_data(item, sensitive_fields) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized


class SecurityValidator:
    """Comprehensive security validator"""
    
    def __init__(self):
        """Initialize security validator"""
        self.input_validator = InputValidator()
        self.output_sanitizer = OutputSanitizer()
        logger.info("SecurityValidator initialized")
    
    def validate_input(self, data: Any, schema: Optional[Dict[str, Any]] = None) -> tuple[bool, Optional[str]]:
        """Validate input data"""
        if isinstance(data, str):
            return self.input_validator.validate_string(data)
        elif isinstance(data, dict):
            return self.input_validator.validate_dict(data, schema)
        else:
            return True, None
    
    def sanitize_output(self, data: Any) -> Any:
        """Sanitize output data"""
        return self.output_sanitizer.sanitize_output(data)
    
    def sanitize_for_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for logging (remove sensitive fields)"""
        return self.output_sanitizer.remove_sensitive_data(data)

