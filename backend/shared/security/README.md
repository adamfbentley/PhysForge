# Security Middleware and Validation

## Overview
This module contains security-related middleware, validation functions, and security utilities for the PhysForge platform.

## Components
- `rate_limiting.py` - Rate limiting middleware
- `input_validation.py` - Input sanitization and validation
- `cors_middleware.py` - CORS configuration
- `security_headers.py` - Security headers middleware
- `audit_logging.py` - Security event logging

## Security Features
- Rate limiting per user/IP
- Input validation and sanitization
- CORS protection
- Security headers (HSTS, CSP, X-Frame-Options)
- Audit logging for security events
- File upload restrictions
- SQL injection prevention