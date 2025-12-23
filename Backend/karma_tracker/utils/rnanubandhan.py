"""
Rnanubandhan Relationship Module

This module implements the karmic debt network linking users via debtor-receiver relationships.
It tracks karmic debts, repayments, and transfers between users.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from database import rnanubandhan_col, users_col
from bson import ObjectId

class RnanubandhanManager:
    """Manages Rnanubandhan (karmic debt) relationships between users"""
    
    def __init__(self):
        """Initialize the Rnanubandhan manager"""
        pass
    
    def create_debt_relationship(self, debtor_id: str, receiver_id: str, 
                               action_type: str, severity: str, 
                               amount: float, description: str = "") -> Dict[str, Any]:
        """
        Create a karmic debt relationship between two users.
        
        Args:
            debtor_id (str): User ID of the debtor
            receiver_id (str): User ID of the receiver
            action_type (str): Type of action that created the debt
            severity (str): Severity level (minor, medium, major)
            amount (float): Amount of karmic debt
            description (str): Description of the debt
            
        Returns:
            dict: Created relationship document
        """
        # Validate that debtor and receiver are different users
        if debtor_id == receiver_id:
            raise ValueError("Debtor and receiver cannot be the same user")
        
        # Validate users exist
        debtor = users_col.find_one({"user_id": debtor_id})
        receiver = users_col.find_one({"user_id": receiver_id})
        
        if not debtor:
            raise ValueError(f"Debtor user {debtor_id} not found")
        if not receiver:
            raise ValueError(f"Receiver user {receiver_id} not found")
        
        # Create relationship document
        relationship = {
            "debtor_id": debtor_id,
            "receiver_id": receiver_id,
            "action_type": action_type,
            "severity": severity,
            "amount": amount,
            "description": description,
            "status": "active",  # active, repaid, transferred
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "repayment_history": []
        }
        
        # Insert into database
        result = rnanubandhan_col.insert_one(relationship)
        relationship["_id"] = str(result.inserted_id)
        
        return relationship
    
    def get_user_debts(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all karmic debts for a user (where user is the debtor).
        
        Args:
            user_id (str): User ID
            status (str, optional): Filter by status (active, repaid, transferred)
            
        Returns:
            list: List of debt relationships
        """
        query = {"debtor_id": user_id}
        if status:
            query["status"] = status
            
        relationships = list(rnanubandhan_col.find(query))
        return self._serialize_relationships(relationships)
    
    def get_user_credits(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all karmic credits for a user (where user is the receiver).
        
        Args:
            user_id (str): User ID
            status (str, optional): Filter by status (active, repaid, transferred)
            
        Returns:
            list: List of credit relationships
        """
        query = {"receiver_id": user_id}
        if status:
            query["status"] = status
            
        relationships = list(rnanubandhan_col.find(query))
        return self._serialize_relationships(relationships)
    
    def get_network_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of a user's Rnanubandhan network.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Network summary
        """
        # Get debts (user owes to others)
        debts = self.get_user_debts(user_id, "active")
        total_debt = sum(debt["amount"] for debt in debts)
        
        # Get credits (others owe to user)
        credits = self.get_user_credits(user_id, "active")
        total_credit = sum(credit["amount"] for credit in credits)
        
        # Get unique connections
        debtors = set(debt["receiver_id"] for debt in debts)
        creditors = set(credit["debtor_id"] for credit in credits)
        
        return {
            "user_id": user_id,
            "total_debt": total_debt,
            "total_credit": total_credit,
            "net_position": total_credit - total_debt,
            "active_debts": len(debts),
            "active_credits": len(credits),
            "unique_debtors": list(debtors),
            "unique_creditors": list(creditors),
            "relationship_count": len(debtors) + len(creditors)
        }
    
    def repay_debt(self, relationship_id: str, amount: float, 
                   repayment_method: str = "atonement") -> Dict[str, Any]:
        """
        Repay a karmic debt.
        
        Args:
            relationship_id (str): ID of the relationship
            amount (float): Amount to repay
            repayment_method (str): Method of repayment (atonement, service, etc.)
            
        Returns:
            dict: Updated relationship
        """
        # Validate that the relationship_id is a valid ObjectId format
        try:
            object_id = ObjectId(relationship_id)
        except Exception:
            raise ValueError(f"Invalid relationship ID format: {relationship_id}. Must be a valid ObjectId.")
        
        # Find the relationship
        relationship = rnanubandhan_col.find_one({"_id": object_id})
        if not relationship:
            raise ValueError(f"Relationship {relationship_id} not found")
        
        # Validate amount
        if amount <= 0:
            raise ValueError("Repayment amount must be positive")
        
        if amount > relationship["amount"]:
            raise ValueError("Repayment amount cannot exceed debt amount")
        
        # Record repayment
        repayment_record = {
            "amount": amount,
            "method": repayment_method,
            "timestamp": datetime.now(timezone.utc)
        }
        
        # Update relationship
        new_amount = relationship["amount"] - amount
        update_fields = {
            "amount": new_amount,
            "updated_at": datetime.now(timezone.utc)
        }
        
        # If fully repaid, update status
        if new_amount <= 0:
            update_fields["status"] = "repaid"
            update_fields["amount"] = 0
        
        # Use $set for regular fields and $push for array updates
        rnanubandhan_col.update_one(
            {"_id": object_id},
            {
                "$set": update_fields,
                "$push": {"repayment_history": repayment_record}
            }
        )
        
        # Return updated relationship
        updated_relationship = rnanubandhan_col.find_one({"_id": object_id})
        return self._serialize_relationship(updated_relationship)
    
    def transfer_debt(self, relationship_id: str, new_debtor_id: str) -> Dict[str, Any]:
        """
        Transfer a karmic debt to another user.
        
        Args:
            relationship_id (str): ID of the relationship
            new_debtor_id (str): User ID of the new debtor
            
        Returns:
            dict: New relationship document
        """
        # Validate that the relationship_id is a valid ObjectId format
        try:
            object_id = ObjectId(relationship_id)
        except Exception:
            raise ValueError(f"Invalid relationship ID format: {relationship_id}. Must be a valid ObjectId.")
        
        # Find the relationship
        relationship = rnanubandhan_col.find_one({"_id": object_id})
        if not relationship:
            raise ValueError(f"Relationship {relationship_id} not found")
        
        # Validate new debtor exists
        new_debtor = users_col.find_one({"user_id": new_debtor_id})
        if not new_debtor:
            raise ValueError(f"New debtor user {new_debtor_id} not found")
        
        # Create new relationship with new debtor
        new_relationship = {
            "debtor_id": new_debtor_id,
            "receiver_id": relationship["receiver_id"],
            "action_type": relationship["action_type"],
            "severity": relationship["severity"],
            "amount": relationship["amount"],
            "description": f"Transferred from {relationship['debtor_id']}: {relationship['description']}",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "repayment_history": relationship.get("repayment_history", []).copy()
        }
        
        # Insert new relationship
        result = rnanubandhan_col.insert_one(new_relationship)
        new_relationship["_id"] = str(result.inserted_id)
        
        # Mark original relationship as transferred
        rnanubandhan_col.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "status": "transferred",
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return self._serialize_relationship(new_relationship)
    
    def get_relationship_by_id(self, relationship_id: str) -> Dict[str, Any]:
        """
        Get a specific relationship by ID.
        
        Args:
            relationship_id (str): ID of the relationship
            
        Returns:
            dict: Relationship document
        """
        # Validate that the relationship_id is a valid ObjectId format
        try:
            object_id = ObjectId(relationship_id)
        except Exception:
            raise ValueError(f"Invalid relationship ID format: {relationship_id}. Must be a valid ObjectId.")
        
        relationship = rnanubandhan_col.find_one({"_id": object_id})
        if not relationship:
            raise ValueError(f"Relationship {relationship_id} not found")
        
        return self._serialize_relationship(relationship)
    
    def _serialize_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """Serialize a list of relationships (convert ObjectId to string)"""
        serialized = []
        for rel in relationships:
            serialized.append(self._serialize_relationship(rel))
        return serialized
    
    def _serialize_relationship(self, relationship: Dict) -> Dict:
        """Serialize a relationship (convert ObjectId to string)"""
        if "_id" in relationship:
            relationship["_id"] = str(relationship["_id"])
        return relationship

# Global instance
rnanubandhan_manager = RnanubandhanManager()