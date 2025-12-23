"""
Comprehensive input validation for KarmaChain API endpoints
Provides robust validation for all user inputs with detailed error messages
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import re
import html
from enum import Enum
from config import ACTIONS

# Validation constants
MAX_USER_ID_LENGTH = 50
MAX_ACTION_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 500
MAX_CONTEXT_LENGTH = 1000
MAX_METADATA_SIZE = 1024  # 1KB limit for metadata
MIN_INTENSITY = 0.1
MAX_INTENSITY = 5.0
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = ['.txt', '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx']

# Severity levels (must match config.py)
class SeverityLevel(str, Enum):
    MINOR = "minor"
    MEDIUM = "medium"
    MAJOR = "major"
    MAHA = "maha"

# Event types (must match API implementation)
class EventType(str, Enum):
    LIFE_EVENT = "life_event"
    APPEAL = "appeal"
    ATONEMENT = "atonement"
    ATONEMENT_WITH_FILE = "atonement_with_file"
    DEATH_EVENT = "death_event"
    STATS_REQUEST = "stats_request"

# Roles (must match config.py)
class UserRole(str, Enum):
    LEARNER = "learner"
    VOLUNTEER = "volunteer"
    SEVA = "seva"
    GURU = "guru"

# Action types (validated against known actions)
ALLOWED_ACTIONS = set(ACTIONS)

class ValidatedLogActionRequest(BaseModel):
    """Enhanced LogActionRequest with comprehensive validation"""
    user_id: str = Field(..., min_length=1, max_length=MAX_USER_ID_LENGTH)
    role: UserRole
    action: str = Field(..., min_length=1, max_length=MAX_ACTION_LENGTH)
    intensity: Optional[float] = Field(default=1.0, ge=MIN_INTENSITY, le=MAX_INTENSITY)
    context: Optional[str] = Field(default=None, max_length=MAX_CONTEXT_LENGTH)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('User ID must contain only alphanumeric characters, underscores, and hyphens')
        return v
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ALLOWED_ACTIONS:
            raise ValueError(f'Action must be one of: {", ".join(sorted(ALLOWED_ACTIONS))}')
        return v
    
    @validator('context')
    def validate_context(cls, v):
        if v and len(v.strip()) == 0:
            raise ValueError('Context cannot be empty or whitespace only')
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        if v:
            # Check metadata size (rough estimation)
            metadata_str = str(v)
            if len(metadata_str.encode('utf-8')) > MAX_METADATA_SIZE:
                raise ValueError(f'Metadata size exceeds maximum allowed size of {MAX_METADATA_SIZE} bytes')
        return v

class ValidatedRedeemRequest(BaseModel):
    """Enhanced RedeemRequest with validation"""
    user_id: str = Field(..., min_length=1, max_length=MAX_USER_ID_LENGTH)
    token_type: str = Field(..., min_length=1, max_length=50)
    amount: float = Field(..., gt=0, le=1000000)  # Max 1M tokens
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('User ID must contain only alphanumeric characters, underscores, and hyphens')
        return v
    
    @validator('token_type')
    def validate_token_type(cls, v):
        allowed_tokens = {
            "DharmaPoints", "SevaPoints", "PunyaTokens", "DridhaKarma",
            "AdridhaKarma", "SanchitaKarma", "PrarabdhaKarma"
        }
        if v not in allowed_tokens:
            raise ValueError(f'Token type must be one of: {", ".join(sorted(allowed_tokens))}')
        return v

class ValidatedKarmaEvent(BaseModel):
    """Enhanced KarmaEvent with validation"""
    event_id: str = Field(..., min_length=1, max_length=100)
    event_type: EventType
    user_id: str = Field(..., min_length=1, max_length=MAX_USER_ID_LENGTH)
    data: Dict[str, Any]
    timestamp: datetime
    source: Optional[str] = Field(default=None, max_length=100)
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('event_id')
    def validate_event_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Event ID must contain only alphanumeric characters, underscores, and hyphens')
        return v
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('User ID must contain only alphanumeric characters, underscores, and hyphens')
        return v
    
    @validator('data')
    def validate_event_data(cls, v, values):
        event_type = values.get('event_type')
        if event_type == EventType.LIFE_EVENT:
            if 'action_type' not in v:
                raise ValueError('Life event must include action_type')
            if 'description' not in v:
                raise ValueError('Life event must include description')
            if len(v.get('description', '')) > MAX_DESCRIPTION_LENGTH:
                raise ValueError(f'Description exceeds maximum length of {MAX_DESCRIPTION_LENGTH}')
        
        elif event_type == EventType.ATONEMENT:
            if 'action_id' not in v:
                raise ValueError('Atonement must include action_id')
            if 'severity' in v and v['severity'] not in [s.value for s in SeverityLevel]:
                raise ValueError(f'Severity must be one of: {", ".join([s.value for s in SeverityLevel])}')
        
        return v

class ValidatedAtonementRequest(BaseModel):
    """Validation for atonement requests"""
    user_id: str = Field(..., min_length=1, max_length=MAX_USER_ID_LENGTH)
    plan_id: str = Field(..., min_length=1, max_length=100)
    atonement_type: str = Field(..., min_length=1, max_length=50)
    amount: Optional[float] = Field(default=None, gt=0)
    proof_text: Optional[str] = Field(default=None, max_length=2000)
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('User ID must contain only alphanumeric characters, underscores, and hyphens')
        return v
    
    @validator('atonement_type')
    def validate_atonement_type(cls, v):
        allowed_types = {"Jap", "Tap", "Bhakti", "Daan", "Seva", "Meditation"}
        if v not in allowed_types:
            raise ValueError(f'Atonement type must be one of: {", ".join(sorted(allowed_types))}')
        return v
    
    @validator('proof_text')
    def validate_proof_text(cls, v):
        if v and len(v.strip()) == 0:
            raise ValueError('Proof text cannot be empty or whitespace only')
        return v

class ValidatedFileUpload(BaseModel):
    """Validation for file uploads"""
    filename: str
    content_type: str
    size: int
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Filename cannot be empty')
        
        # Check file extension
        ext = '.' + v.split('.')[-1].lower() if '.' in v else ''
        if ext not in ALLOWED_FILE_TYPES:
            raise ValueError(f'File type not allowed. Allowed types: {", ".join(ALLOWED_FILE_TYPES)}')
        
        return v
    
    @validator('size')
    def validate_file_size(cls, v):
        if v > MAX_FILE_SIZE:
            raise ValueError(f'File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f}MB')
        return v
    
    @validator('content_type')
    def validate_content_type(cls, v):
        allowed_content_types = {
            'text/plain', 'application/pdf', 'image/jpeg', 'image/jpg', 
            'image/png', 'image/gif', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        if v not in allowed_content_types:
            raise ValueError(f'Content type not allowed: {v}')
        return v

def validate_user_input(data: Dict[str, Any], model_class) -> tuple[bool, Optional[str]]:
    """
    Validate user input against a Pydantic model
    
    Args:
        data: Input data to validate
        model_class: Pydantic model class to validate against
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        model_class(**data)
        return True, None
    except Exception as e:
        return False, str(e)

def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks
    
    Args:
        text: Input text to sanitize
    
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    # Escape HTML special characters to neutralize tags and quotes
    escaped = html.escape(text.strip(), quote=True)
    
    # Limit length
    if len(escaped) > 1000:
        escaped = escaped[:1000]
    
    return escaped

def validate_karma_action(action: str, severity: str, description: str) -> tuple[bool, Optional[str]]:
    """
    Validate karma action parameters
    
    Args:
        action: Action type
        severity: Severity level
        description: Action description
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if action not in ALLOWED_ACTIONS:
        return False, f"Invalid action type: {action}. Must be one of: {', '.join(sorted(ALLOWED_ACTIONS))}"
    
    if severity not in [s.value for s in SeverityLevel]:
        return False, f"Invalid severity: {severity}. Must be one of: {', '.join([s.value for s in SeverityLevel])}"
    
    if not description or len(description.strip()) == 0:
        return False, "Description cannot be empty"
    
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return False, f"Description exceeds maximum length of {MAX_DESCRIPTION_LENGTH} characters"
    
    return True, None