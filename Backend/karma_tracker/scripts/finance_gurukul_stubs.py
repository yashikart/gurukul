#!/usr/bin/env python3
"""
Test stubs for Finance and Gurukul modules
Demonstrates how external modules can send data to the normalization API
"""
import requests
import json
import time
import uuid
from datetime import datetime

# Base URL for the normalization API
NORMALIZATION_API_URL = "http://localhost:8000/api/v1"

class FinanceModuleStub:
    """Stub for Finance module"""
    
    def __init__(self):
        self.module_name = "finance"
        
    def process_transaction(self, transaction_id, amount, transaction_type, user_id):
        """Simulate processing a financial transaction"""
        print(f"Finance: Processing {transaction_type} transaction {transaction_id} for user {user_id}")
        
        # Determine raw value based on transaction type and amount
        if transaction_type == "deposit":
            raw_value = amount * 0.1  # Positive karma for deposits
        elif transaction_type == "withdrawal":
            raw_value = -amount * 0.05  # Slight negative karma for withdrawals
        elif transaction_type == "purchase":
            raw_value = -amount * 0.02  # Small negative karma for purchases
        else:
            raw_value = 0  # Neutral for other transactions
            
        # Send to normalization API
        return self._send_to_normalization_api(transaction_id, "transaction", raw_value, {
            "transaction_type": transaction_type,
            "amount": amount,
            "currency": "USD"
        }, {
            "user_id": user_id
        })
    
    def _send_to_normalization_api(self, action_id, action_type, raw_value, context, metadata):
        """Send data to normalization API"""
        payload = {
            "module": self.module_name,
            "action_type": action_type,
            "raw_value": raw_value,
            "context": context,
            "metadata": metadata
        }
        
        try:
            response = requests.post(f"{NORMALIZATION_API_URL}/normalize_state", json=payload)
            if response.status_code == 200:
                normalized_data = response.json()
                print(f"Finance: Normalized state created with ID {normalized_data['state_id']}")
                return normalized_data
            else:
                print(f"Finance: Error sending to normalization API: {response.text}")
                return None
        except Exception as e:
            print(f"Finance: Exception sending to normalization API: {e}")
            return None

class GurukulModuleStub:
    """Stub for Gurukul module"""
    
    def __init__(self):
        self.module_name = "gurukul"
        
    def complete_lesson(self, lesson_id, user_id, subject, score):
        """Simulate completing a lesson"""
        print(f"Gurukul: User {user_id} completed lesson {lesson_id} in {subject} with score {score}")
        
        # Determine raw value based on score
        raw_value = score  # Use score directly as raw value
            
        # Send to normalization API
        return self._send_to_normalization_api(lesson_id, "lesson_completed", raw_value, {
            "subject": subject,
            "score": score
        }, {
            "user_id": user_id
        })
    
    def pass_quiz(self, quiz_id, user_id, subject, score):
        """Simulate passing a quiz"""
        print(f"Gurukul: User {user_id} passed quiz {quiz_id} in {subject} with score {score}")
        
        # Determine raw value based on score (quizzes are more valuable)
        raw_value = score * 1.5  # Quiz performance is weighted higher
            
        # Send to normalization API
        return self._send_to_normalization_api(quiz_id, "quiz_passed", raw_value, {
            "subject": subject,
            "score": score
        }, {
            "user_id": user_id
        })
    
    def _send_to_normalization_api(self, action_id, action_type, raw_value, context, metadata):
        """Send data to normalization API"""
        payload = {
            "module": self.module_name,
            "action_type": action_type,
            "raw_value": raw_value,
            "context": context,
            "metadata": metadata
        }
        
        try:
            response = requests.post(f"{NORMALIZATION_API_URL}/normalize_state", json=payload)
            if response.status_code == 200:
                normalized_data = response.json()
                print(f"Gurukul: Normalized state created with ID {normalized_data['state_id']}")
                return normalized_data
            else:
                print(f"Gurukul: Error sending to normalization API: {response.text}")
                return None
        except Exception as e:
            print(f"Gurukul: Exception sending to normalization API: {e}")
            return None

def run_demo():
    """Run a demonstration of both modules sending data to the normalization API"""
    print("Starting Behavioral State Normalization Demo")
    print("=" * 50)
    
    # Initialize module stubs
    finance_stub = FinanceModuleStub()
    gurukul_stub = GurukulModuleStub()
    
    # Demo Finance transactions
    print("\n--- Finance Module Demo ---")
    finance_stub.process_transaction("txn_001", 1000.0, "deposit", "user_finance_001")
    time.sleep(1)
    
    finance_stub.process_transaction("txn_002", 250.0, "purchase", "user_finance_001")
    time.sleep(1)
    
    finance_stub.process_transaction("txn_003", 500.0, "withdrawal", "user_finance_002")
    time.sleep(1)
    
    # Demo Gurukul activities
    print("\n--- Gurukul Module Demo ---")
    gurukul_stub.complete_lesson("lesson_math_001", "user_gurukul_001", "Mathematics", 85.5)
    time.sleep(1)
    
    gurukul_stub.pass_quiz("quiz_physics_001", "user_gurukul_001", "Physics", 92.0)
    time.sleep(1)
    
    gurukul_stub.complete_lesson("lesson_history_001", "user_gurukul_002", "History", 78.0)
    time.sleep(1)
    
    # Demo batch processing
    print("\n--- Batch Processing Demo ---")
    batch_payload = {
        "states": [
            {
                "module": "finance",
                "action_type": "investment",
                "raw_value": 2000.0,
                "context": {"type": "mutual_fund"},
                "metadata": {"user_id": "user_finance_003"}
            },
            {
                "module": "gurukul",
                "action_type": "assignment_submitted",
                "raw_value": 95.0,
                "context": {"subject": "chemistry"},
                "metadata": {"user_id": "user_gurukul_003"}
            }
        ]
    }
    
    try:
        response = requests.post(f"{NORMALIZATION_API_URL}/normalize_state/batch", json=batch_payload)
        if response.status_code == 200:
            normalized_data = response.json()
            print(f"Batch processing completed. Created {len(normalized_data)} normalized states:")
            for state in normalized_data:
                print(f"  - State ID: {state['state_id']}, Module: {state['module']}, Value: {state['feedback_value']}")
        else:
            print(f"Batch processing failed: {response.text}")
    except Exception as e:
        print(f"Exception during batch processing: {e}")
    
    print("\n" + "=" * 50)
    print("Demo completed successfully!")

if __name__ == "__main__":
    run_demo()