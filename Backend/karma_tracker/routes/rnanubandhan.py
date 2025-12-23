"""
Rnanubandhan API Routes

This module provides API endpoints for managing Rnanubandhan (karmic debt) relationships.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from utils.rnanubandhan import rnanubandhan_manager
from validation_middleware import validation_dependency

router = APIRouter()

class CreateDebtRequest(BaseModel):
    """Request model for creating a karmic debt relationship"""
    debtor_id: str
    receiver_id: str
    action_type: str
    severity: str
    amount: float
    description: Optional[str] = ""

class RepayDebtRequest(BaseModel):
    """Request model for repaying a karmic debt"""
    relationship_id: str
    amount: float
    repayment_method: Optional[str] = "atonement"

class TransferDebtRequest(BaseModel):
    """Request model for transferring a karmic debt"""
    relationship_id: str
    new_debtor_id: str

@router.get("/api/v1/rnanubandhan/{user_id}")
async def get_rnanubandhan_network(user_id: str, _: bool = Depends(validation_dependency)):
    """
    Get a user's complete Rnanubandhan network including debts and credits.
    
    Args:
        user_id (str): The ID of the user
        
    Returns:
        dict: User's Rnanubandhan network summary
    """
    try:
        # Get network summary
        network_summary = rnanubandhan_manager.get_network_summary(user_id)
        
        # Get detailed debts and credits
        debts = rnanubandhan_manager.get_user_debts(user_id)
        credits = rnanubandhan_manager.get_user_credits(user_id)
        
        return {
            "status": "success",
            "user_id": user_id,
            "network_summary": network_summary,
            "debts": debts,
            "credits": credits
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving Rnanubandhan network: {str(e)}")

@router.get("/api/v1/rnanubandhan/{user_id}/debts")
async def get_user_debts(user_id: str, status: Optional[str] = None, _: bool = Depends(validation_dependency)):
    """
    Get a user's karmic debts.
    
    Args:
        user_id (str): The ID of the user
        status (str, optional): Filter by status (active, repaid, transferred)
        
    Returns:
        dict: User's karmic debts
    """
    try:
        debts = rnanubandhan_manager.get_user_debts(user_id, status)
        return {
            "status": "success",
            "user_id": user_id,
            "debts": debts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving debts: {str(e)}")

@router.get("/api/v1/rnanubandhan/{user_id}/credits")
async def get_user_credits(user_id: str, status: Optional[str] = None, _: bool = Depends(validation_dependency)):
    """
    Get a user's karmic credits.
    
    Args:
        user_id (str): The ID of the user
        status (str, optional): Filter by status (active, repaid, transferred)
        
    Returns:
        dict: User's karmic credits
    """
    try:
        credits = rnanubandhan_manager.get_user_credits(user_id, status)
        return {
            "status": "success",
            "user_id": user_id,
            "credits": credits
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving credits: {str(e)}")

@router.post("/api/v1/rnanubandhan/create-debt")
async def create_debt_relationship(request: CreateDebtRequest, _: bool = Depends(validation_dependency)):
    """
    Create a karmic debt relationship between two users.
    
    Args:
        request (CreateDebtRequest): Debt creation request
        
    Returns:
        dict: Created relationship
    """
    try:
        relationship = rnanubandhan_manager.create_debt_relationship(
            request.debtor_id,
            request.receiver_id,
            request.action_type,
            request.severity,
            request.amount,
            request.description
        )
        return {
            "status": "success",
            "message": "Karmic debt relationship created successfully",
            "relationship": relationship
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating debt relationship: {str(e)}")

@router.post("/api/v1/rnanubandhan/repay-debt")
async def repay_debt(request: RepayDebtRequest, _: bool = Depends(validation_dependency)):
    """
    Repay a karmic debt.
    
    Args:
        request (RepayDebtRequest): Debt repayment request
        
    Returns:
        dict: Updated relationship
    """
    try:
        updated_relationship = rnanubandhan_manager.repay_debt(
            request.relationship_id,
            request.amount,
            request.repayment_method
        )
        return {
            "status": "success",
            "message": "Karmic debt repayment processed successfully",
            "relationship": updated_relationship
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing debt repayment: {str(e)}")

@router.post("/api/v1/rnanubandhan/transfer-debt")
async def transfer_debt(request: TransferDebtRequest, _: bool = Depends(validation_dependency)):
    """
    Transfer a karmic debt to another user.
    
    Args:
        request (TransferDebtRequest): Debt transfer request
        
    Returns:
        dict: New relationship
    """
    try:
        new_relationship = rnanubandhan_manager.transfer_debt(
            request.relationship_id,
            request.new_debtor_id
        )
        return {
            "status": "success",
            "message": "Karmic debt transferred successfully",
            "relationship": new_relationship
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transferring debt: {str(e)}")

@router.get("/api/v1/rnanubandhan/relationship/{relationship_id}")
async def get_relationship(relationship_id: str, _: bool = Depends(validation_dependency)):
    """
    Get a specific Rnanubandhan relationship by ID.
    
    Args:
        relationship_id (str): The ID of the relationship
        
    Returns:
        dict: Relationship details
    """
    try:
        relationship = rnanubandhan_manager.get_relationship_by_id(relationship_id)
        return {
            "status": "success",
            "relationship": relationship
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving relationship: {str(e)}")