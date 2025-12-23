from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum

# Enums for type safety
class EventStatus(str, Enum):
    """Status values for karma events"""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"

class EventType(str, Enum):
    """Valid event types for unified event gateway"""
    LIFE_EVENT = "life_event"
    ATONEMENT = "atonement"
    ATONEMENT_WITH_FILE = "atonement_with_file"
    APPEAL = "appeal"
    DEATH_EVENT = "death_event"
    STATS_REQUEST = "stats_request"

class AtonementType(str, Enum):
    """Valid atonement types"""
    DAAN = "Daan"
    BHAKTI = "Bhakti"
    TAP = "Tap"
    JAP = "Jap"

class PaapSeverity(str, Enum):
    """Paap severity levels"""
    MINOR = "minor"
    MEDIUM = "medium"
    MAHA = "maha"

class RnanubandhanSeverity(str, Enum):
    """Rnanubandhan severity levels"""
    MINOR = "minor"
    MEDIUM = "medium"
    MAJOR = "major"

# Request Models
class LogActionRequest(BaseModel):
    """Request model for logging karma actions"""
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    role: str = Field(..., min_length=1, max_length=50, description="User role")
    action: str = Field(..., min_length=1, max_length=100, description="Action performed")
    note: Optional[str] = Field(None, max_length=500, description="Optional note")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "role": "learner",
                "action": "helping_peers",
                "note": "Helped a colleague debug code"
            }
        }

class RedeemRequest(BaseModel):
    """Request model for redeeming tokens"""
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    token_type: str = Field(..., min_length=1, max_length=50, description="Type of token to redeem")
    amount: float = Field(..., gt=0, description="Amount to redeem (must be positive)")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "token_type": "DharmaPoints",
                "amount": 50.0
            }
        }

class AppealRequest(BaseModel):
    """Request model for karma appeals"""
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    action: str = Field(..., min_length=1, max_length=100, description="Action to appeal")
    context: Optional[str] = Field(None, max_length=1000, description="Context for the appeal")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "action": "cheat",
                "context": "It was a misunderstanding"
            }
        }

class AtonementSubmission(BaseModel):
    """Request model for atonement submission"""
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    plan_id: str = Field(..., min_length=1, max_length=100, description="Atonement plan ID")
    atonement_type: str = Field(..., description="Type of atonement (Daan, Bhakti, Tap, Jap)")
    amount: float = Field(..., gt=0, description="Amount completed")
    proof_text: Optional[str] = Field(None, max_length=2000, description="Text proof of completion")
    tx_hash: Optional[str] = Field(None, max_length=100, description="Transaction hash for Daan")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "plan_id": "atonement_001",
                "atonement_type": "Daan",
                "amount": 100.0,
                "proof_text": "Donated to charity",
                "tx_hash": "0x123abc..."
            }
        }

class DeathEventRequest(BaseModel):
    """Request model for death events"""
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123"
            }
        }

class CreateDebtRequest(BaseModel):
    """Request model for creating Rnanubandhan debt relationship"""
    debtor_id: str = Field(..., min_length=1, max_length=100, description="Debtor user ID")
    receiver_id: str = Field(..., min_length=1, max_length=100, description="Receiver user ID")
    action_type: str = Field(..., min_length=1, max_length=100, description="Action that created debt")
    severity: RnanubandhanSeverity = Field(..., description="Severity level")
    amount: float = Field(..., gt=0, description="Debt amount")
    description: Optional[str] = Field("", max_length=500, description="Description of debt")

    class Config:
        json_schema_extra = {
            "example": {
                "debtor_id": "user123",
                "receiver_id": "user456",
                "action_type": "harm_others",
                "severity": "medium",
                "amount": 50.0,
                "description": "Caused emotional harm"
            }
        }

class RepayDebtRequest(BaseModel):
    """Request model for repaying Rnanubandhan debt"""
    relationship_id: str = Field(..., min_length=1, max_length=100, description="Relationship ID")
    amount: float = Field(..., gt=0, description="Amount to repay")
    repayment_method: str = Field(default="atonement", max_length=50, description="Method of repayment")

    class Config:
        json_schema_extra = {
            "example": {
                "relationship_id": "507f1f77bcf86cd799439011",
                "amount": 25.0,
                "repayment_method": "atonement"
            }
        }

class TransferDebtRequest(BaseModel):
    """Request model for transferring Rnanubandhan debt"""
    relationship_id: str = Field(..., min_length=1, max_length=100, description="Relationship ID")
    new_debtor_id: str = Field(..., min_length=1, max_length=100, description="New debtor user ID")

    class Config:
        json_schema_extra = {
            "example": {
                "relationship_id": "507f1f77bcf86cd799439011",
                "new_debtor_id": "user789"
            }
        }

class AgamiPredictionRequest(BaseModel):
    """Request model for Agami karma prediction"""
    user_id: str = Field(..., min_length=1, max_length=100, description="User identifier")
    scenario: Optional[Dict[str, Any]] = Field(None, description="Scenario context for prediction")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "scenario": {
                    "context": {
                        "environment": "gurukul"
                    }
                }
            }
        }

class ContextWeightsRequest(BaseModel):
    """Request model for updating context weights"""
    context_key: str = Field(..., min_length=1, max_length=100, description="Context key")
    weights: Dict[str, float] = Field(..., description="Weight values")

    class Config:
        json_schema_extra = {
            "example": {
                "context_key": "learner_gurukul",
                "weights": {
                    "dharma_weight": 1.2,
                    "artha_weight": 1.1,
                    "kama_weight": 0.9,
                    "moksha_weight": 1.3
                }
            }
        }

# Storage Models
class KarmaEvent(BaseModel):
    """Model for storing unified events in karma_events collection"""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event")
    data: Dict[str, Any] = Field(..., description="Event data payload")
    timestamp: datetime = Field(..., description="Event timestamp")
    source: Optional[str] = Field(None, max_length=100, description="Event source system")
    status: EventStatus = Field(default=EventStatus.PROCESSED, description="Event processing status")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Response data from processing")
    error_message: Optional[str] = Field(None, max_length=1000, description="Error message if failed")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "event_id": "evt_123456",
                "event_type": "life_event",
                "data": {
                    "user_id": "user123",
                    "action": "helping_peers",
                    "role": "learner"
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "source": "unified_gateway",
                "status": "processed"
            }
        }


