"""
Validation middleware for KarmaChain API endpoints
Integrates comprehensive validation into the FastAPI application
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
import time
from validation import (
    ValidatedLogActionRequest, ValidatedRedeemRequest, ValidatedKarmaEvent,
    ValidatedAtonementRequest, ValidatedFileUpload, validate_user_input,
    sanitize_input, validate_karma_action
)

logger = logging.getLogger(__name__)

class ValidationMiddleware:
    """Middleware for comprehensive input validation"""
    
    def __init__(self):
        self.validation_stats = {
            'total_requests': 0,
            'valid_requests': 0,
            'invalid_requests': 0,
            'validation_errors': {}
        }
    
    async def validate_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Validate incoming request based on endpoint
        
        Args:
            request: FastAPI request object
            
        Returns:
            Dict with validation result or None if valid
        """
        self.validation_stats['total_requests'] += 1
        
        try:
            # Determine validation model based on path and method
            path = request.url.path
            method = request.method
            
            # Skip validation for GET requests and other methods that don't have JSON bodies
            if method in ['GET', 'HEAD', 'OPTIONS']:
                self.validation_stats['valid_requests'] += 1
                return None
            
            # Get request body only for methods that typically have bodies
            body = None
            if method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                try:
                    body = await request.json()
                except Exception:
                    # If JSON parsing fails, it might be a form or empty body
                    # For now, we'll skip validation for non-JSON requests
                    self.validation_stats['valid_requests'] += 1
                    return None
            
            if body is None:
                self.validation_stats['valid_requests'] += 1
                return None
            
            # Route-specific validation
            if path.startswith('/log-action') and method == 'POST':
                return await self._validate_log_action(body)
            elif path.startswith('/redeem') and method == 'POST':
                return await self._validate_redeem(body)
            elif path.startswith('/karma/') and method == 'POST':
                return await self._validate_karma_event(body)
            elif path.startswith('/submit-atonement') and method == 'POST':
                return await self._validate_atonement(body)
            elif path.startswith('/upload') and method == 'POST':
                return await self._validate_file_upload(request)
            
            # If no specific validation, do basic sanitization
            return await self._basic_validation(body)
            
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            self.validation_stats['validation_errors'][str(e)] = \
                self.validation_stats['validation_errors'].get(str(e), 0) + 1
            logger.error(error_msg)
            return {'error': error_msg, 'type': 'validation_exception'}
    
    async def _validate_log_action(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate log action request"""
        # Sanitize inputs
        if 'action' in data:
            data['action'] = sanitize_input(data['action'])
        if 'context' in data:
            data['context'] = sanitize_input(data['context'])
        
        # Validate with Pydantic model
        is_valid, error_msg = validate_user_input(data, ValidatedLogActionRequest)
        
        if not is_valid:
            self.validation_stats['invalid_requests'] += 1
            return {'error': error_msg, 'type': 'validation_error', 'field': 'log_action'}
        
        self.validation_stats['valid_requests'] += 1
        return None
    
    async def _validate_redeem(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate redeem request"""
        # Validate with Pydantic model
        is_valid, error_msg = validate_user_input(data, ValidatedRedeemRequest)
        
        if not is_valid:
            self.validation_stats['invalid_requests'] += 1
            return {'error': error_msg, 'type': 'validation_error', 'field': 'redeem'}
        
        self.validation_stats['valid_requests'] += 1
        return None
    
    async def _validate_karma_event(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate karma event"""
        # Sanitize event data
        if 'data' in data:
            if 'description' in data['data']:
                data['data']['description'] = sanitize_input(data['data']['description'])
            if 'action_type' in data['data']:
                data['data']['action_type'] = sanitize_input(data['data']['action_type'])
        
        # Validate with Pydantic model
        is_valid, error_msg = validate_user_input(data, ValidatedKarmaEvent)
        
        if not is_valid:
            self.validation_stats['invalid_requests'] += 1
            return {'error': error_msg, 'type': 'validation_error', 'field': 'karma_event'}
        
        self.validation_stats['valid_requests'] += 1
        return None
    
    async def _validate_atonement(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate atonement request"""
        # Sanitize inputs
        if 'proof_text' in data:
            data['proof_text'] = sanitize_input(data['proof_text'])
        
        # Validate with Pydantic model
        is_valid, error_msg = validate_user_input(data, ValidatedAtonementRequest)
        
        if not is_valid:
            self.validation_stats['invalid_requests'] += 1
            return {'error': error_msg, 'type': 'validation_error', 'field': 'atonement'}
        
        self.validation_stats['valid_requests'] += 1
        return None
    
    async def _validate_file_upload(self, request: Request) -> Optional[Dict[str, Any]]:
        """Validate file upload"""
        try:
            form = await request.form()
            
            if 'file' not in form:
                return {'error': 'No file provided', 'type': 'validation_error', 'field': 'file'}
            
            file = form['file']
            
            # Create validation data
            file_data = {
                'filename': file.filename,
                'content_type': file.content_type or 'application/octet-stream',
                'size': len(await file.read()) if hasattr(file, 'read') else 0
            }
            
            # Reset file position if possible
            if hasattr(file, 'seek'):
                await file.seek(0)
            
            # Validate with Pydantic model
            is_valid, error_msg = validate_user_input(file_data, ValidatedFileUpload)
            
            if not is_valid:
                self.validation_stats['invalid_requests'] += 1
                return {'error': error_msg, 'type': 'validation_error', 'field': 'file_upload'}
            
            self.validation_stats['valid_requests'] += 1
            return None
            
        except Exception as e:
            return {'error': f'File validation error: {str(e)}', 'type': 'validation_error', 'field': 'file_upload'}
    
    async def _basic_validation(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Basic validation for unhandled endpoints"""
        # Check for suspicious patterns
        suspicious_patterns = [
            '<script', 'javascript:', 'onload=', 'onerror=',
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP'
        ]
        
        data_str = str(data).lower()
        for pattern in suspicious_patterns:
            if pattern.lower() in data_str:
                self.validation_stats['invalid_requests'] += 1
                return {
                    'error': f'Suspicious pattern detected: {pattern}',
                    'type': 'security_validation',
                    'field': 'general'
                }
        
        self.validation_stats['valid_requests'] += 1
        return None
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get current validation statistics"""
        total = self.validation_stats['total_requests']
        valid = self.validation_stats['valid_requests']
        
        return {
            **self.validation_stats,
            'validation_rate': (valid / total * 100) if total > 0 else 0,
            'error_breakdown': dict(self.validation_stats['validation_errors'])
        }

# Global validation middleware instance
validation_middleware = ValidationMiddleware()

async def validation_dependency(request: Request) -> bool:
    """
    FastAPI dependency for validation
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if validation passes
        
    Raises:
        HTTPException: If validation fails
    """
    validation_result = await validation_middleware.validate_request(request)
    
    if validation_result:
        error_type = validation_result.get('type', 'validation_error')
        field = validation_result.get('field', 'unknown')
        error_msg = validation_result.get('error', 'Validation failed')
        
        logger.warning(f"Validation failed for {field}: {error_msg}")
        
        raise HTTPException(
            status_code=400,
            detail={
                'error': error_msg,
                'type': error_type,
                'field': field,
                'timestamp': time.time()
            }
        )
    
    return True

def setup_validation_middleware(app):
    """
    Setup validation middleware for FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    
    @app.middleware("http")
    async def add_validation_headers(request: Request, call_next):
        """Add validation headers to response"""
        start_time = time.time()
        
        response = await call_next(request)
        
        # Add validation headers
        response.headers["X-Validation-Service"] = "KarmaChain-Validation-v1"
        response.headers["X-Validation-Timestamp"] = str(int(time.time()))
        
        # Add validation stats if requested
        if request.headers.get("X-Request-Validation-Stats"):
            stats = validation_middleware.get_validation_stats()
            response.headers["X-Validation-Stats"] = str(stats['validation_rate'])
        
        return response
    
    logger.info("Validation middleware setup complete")