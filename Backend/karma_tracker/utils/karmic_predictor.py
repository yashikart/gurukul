"""
Karmic Predictor Module

This module implements advanced karmic features including:
1. Rnanubandhan ledger tracking
2. Karma cycle simulation (Sanchita → Prarabdha → Agami)
3. Dridha/Adridha scoring influence on predictive guidance
4. Behavior analytics and predictive suggestions
"""

import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any
from database import users_col
from utils.karma_schema import get_karma_weights, calculate_weighted_karma_score
from utils.loka import calculate_net_karma
from utils.paap import get_total_paap_score
from utils.merit import compute_user_merit_score
from config import TOKEN_ATTRIBUTES

class KarmicPredictor:
    """Advanced karmic prediction and analytics engine"""
    
    def __init__(self):
        """Initialize the karmic predictor"""
        pass
    
    def get_rnanubandhan_ledger(self, user_doc: Dict) -> Dict[str, Any]:
        """
        Get the complete Rnanubandhan ledger for a user.
        
        Args:
            user_doc (dict): User document from database
            
        Returns:
            dict: Rnanubandhan ledger with details
        """
        balances = user_doc.get("balances", {})
        rnanubandhan = balances.get("Rnanubandhan", {})
        
        # If Rnanubandhan is not a dict, initialize it
        if not isinstance(rnanubandhan, dict):
            rnanubandhan = {}
            
        # Calculate total debt and severity breakdown
        total_debt = 0
        severity_breakdown = {}
        
        for severity, amount in rnanubandhan.items():
            if severity in TOKEN_ATTRIBUTES.get("Rnanubandhan", {}).get("severity_classes", {}):
                multiplier = TOKEN_ATTRIBUTES["Rnanubandhan"]["severity_classes"][severity]["multiplier"]
                weighted_amount = amount * multiplier
                severity_breakdown[severity] = {
                    "amount": amount,
                    "weighted_amount": weighted_amount,
                    "multiplier": multiplier
                }
                total_debt += weighted_amount
            else:
                # Handle legacy data or unknown severity
                severity_breakdown[severity] = {
                    "amount": amount,
                    "weighted_amount": amount,
                    "multiplier": 1.0
                }
                total_debt += amount
        
        return {
            "ledger": rnanubandhan,
            "severity_breakdown": severity_breakdown,
            "total_debt": total_debt,
            "unpaid_obligations": len(rnanubandhan)
        }
    
    def simulate_karma_cycle(self, user_doc: Dict) -> Dict[str, Any]:
        """
        Simulate the karma cycle: Sanchita → Prarabdha → Agami.
        
        Args:
            user_doc (dict): User document from database
            
        Returns:
            dict: Karma cycle simulation results
        """
        balances = user_doc.get("balances", {})
        
        # Get current karma balances
        sanchita = balances.get("SanchitaKarma", 0)
        prarabdha = balances.get("PrarabdhaKarma", 0)
        dridha = balances.get("DridhaKarma", 0)
        adridha = balances.get("AdridhaKarma", 0)
        
        # Calculate karma that will be experienced in this life (Prarabdha)
        # This is a portion of Sanchita that becomes active
        karma_to_experience = sanchita * 0.3  # 30% of Sanchita becomes Prarabdha
        
        # Calculate new karma being created (Agami) based on recent actions
        # For simulation, we'll use a simplified approach
        merit_score = compute_user_merit_score(user_doc)
        paap_score = get_total_paap_score(user_doc)
        net_karma_change = merit_score - paap_score
        
        # Distribute new karma between Dridha and Adridha based on user's tendencies
        dridha_influence = dridha / (dridha + adridha + 1)  # +1 to avoid division by zero
        adridha_influence = adridha / (dridha + adridha + 1)
        
        new_dridha = net_karma_change * dridha_influence * 0.7  # 70% becomes stable karma
        new_adridha = net_karma_change * adridha_influence * 0.3  # 30% becomes volatile karma
        
        # Update Sanchita (accumulated karma)
        new_sanchita = sanchita + (net_karma_change * 0.5)  # 50% accumulates
        
        return {
            "current": {
                "sanchita": sanchita,
                "prarabdha": prarabdha,
                "dridha": dridha,
                "adridha": adridha
            },
            "cycle_effects": {
                "karma_to_experience": karma_to_experience,
                "new_dridha": new_dridha,
                "new_adridha": new_adridha,
                "new_sanchita": new_sanchita
            },
            "predictions": {
                "future_prarabdha": prarabdha + karma_to_experience,
                "future_sanchita": new_sanchita,
                "future_dridha": dridha + new_dridha,
                "future_adridha": adridha + new_adridha
            }
        }
    
    def analyze_dridha_adridha_influence(self, user_doc: Dict) -> Dict[str, Any]:
        """
        Analyze the influence of Dridha/Adridha scoring on predictive guidance.
        
        Args:
            user_doc (dict): User document from database
            
        Returns:
            dict: Dridha/Adridha influence analysis
        """
        balances = user_doc.get("balances", {})
        dridha = balances.get("DridhaKarma", 0)
        adridha = balances.get("AdridhaKarma", 0)
        
        # Calculate influence factors
        total_stable = dridha + adridha
        if total_stable == 0:
            dridha_ratio = 0.5
            adridha_ratio = 0.5
        else:
            dridha_ratio = dridha / total_stable
            adridha_ratio = adridha / total_stable
        
        # Determine guidance effectiveness
        if dridha_ratio > 0.7:
            # High Dridha - corrective actions more effective
            guidance_effectiveness = "high"
            recommendation = "Corrective actions are likely to be very effective due to strong stable karma patterns"
        elif dridha_ratio > 0.4:
            # Moderate Dridha - corrective actions moderately effective
            guidance_effectiveness = "moderate"
            recommendation = "Corrective actions should be effective with consistent practice"
        else:
            # Low Dridha - need more guidance
            guidance_effectiveness = "low"
            recommendation = "More guidance and repeated corrective actions may be needed due to volatile karma patterns"
        
        return {
            "dridha_score": dridha,
            "adridha_score": adridha,
            "dridha_ratio": dridha_ratio,
            "adridha_ratio": adridha_ratio,
            "guidance_effectiveness": guidance_effectiveness,
            "recommendation": recommendation,
            "implications": {
                "high_dridha": dridha_ratio > 0.7,
                "high_adridha": adridha_ratio > 0.7,
                "balanced_karma": 0.3 <= dridha_ratio <= 0.7
            }
        }
    
    def predict_behavioral_trends(self, user_doc: Dict, action_history = None) -> Dict[str, Any]:
        """
        Predict behavioral trends based on karma patterns.
        
        Args:
            user_doc (dict): User document from database
            action_history (list): Optional list of past actions for trend analysis
            
        Returns:
            dict: Behavioral trend predictions
        """
        # Get current karma state
        net_karma = calculate_net_karma(user_doc)
        merit_score = compute_user_merit_score(user_doc)
        paap_score = get_total_paap_score(user_doc)
        weighted_karma = calculate_weighted_karma_score(user_doc)
        
        # Get Dridha/Adridha analysis
        da_analysis = self.analyze_dridha_adridha_influence(user_doc)
        
        # Get Rnanubandhan analysis
        rnanubandhan_ledger = self.get_rnanubandhan_ledger(user_doc)
        
        # Predict future trends
        predictions = []
        
        # Prediction 1: Based on net karma trend
        if net_karma > 50:
            predictions.append({
                "type": "positive_growth",
                "confidence": 0.85,
                "description": "Positive karmic trajectory indicates continued spiritual growth",
                "suggestion": "Continue current positive practices"
            })
        elif net_karma > 0:
            predictions.append({
                "type": "stable_growth",
                "confidence": 0.75,
                "description": "Stable karmic state with potential for growth",
                "suggestion": "Maintain current practices while exploring new positive actions"
            })
        else:
            predictions.append({
                "type": "improvement_needed",
                "confidence": 0.9,
                "description": "Negative karmic balance requires corrective actions",
                "suggestion": "Focus on atonement and positive actions to improve karma"
            })
        
        # Prediction 2: Based on Dridha/Adridha ratio
        if da_analysis["dridha_ratio"] > 0.7:
            predictions.append({
                "type": "stable_patterns",
                "confidence": 0.8,
                "description": "Strong stable karma patterns indicate consistent behavior",
                "suggestion": "Corrective actions will be highly effective"
            })
        elif da_analysis["adridha_ratio"] > 0.7:
            predictions.append({
                "type": "volatile_patterns",
                "confidence": 0.7,
                "description": "Volatile karma patterns suggest inconsistent behavior",
                "suggestion": "Consistent practice needed to establish stable positive patterns"
            })
        
        # Prediction 3: Based on Rnanubandhan debt
        if rnanubandhan_ledger["total_debt"] > 20:
            predictions.append({
                "type": "karmic_debt",
                "confidence": 0.85,
                "description": "Significant karmic debt may create obstacles",
                "suggestion": "Prioritize atonement practices to reduce karmic debt"
            })
        
        # Calculate overall guidance score
        guidance_score = self._calculate_guidance_score(user_doc, da_analysis, rnanubandhan_ledger)
        
        return {
            "current_state": {
                "net_karma": net_karma,
                "merit_score": merit_score,
                "paap_score": paap_score,
                "weighted_karma": weighted_karma
            },
            "dridha_adridha_analysis": da_analysis,
            "rnanubandhan_analysis": rnanubandhan_ledger,
            "predictions": predictions,
            "guidance_score": guidance_score,
            "next_actions": self._suggest_next_actions(user_doc, predictions)
        }
    
    def _calculate_guidance_score(self, user_doc: Dict, da_analysis: Dict, rnanubandhan_ledger: Dict) -> float:
        """
        Calculate a guidance score based on various karmic factors.
        
        Args:
            user_doc (dict): User document
            da_analysis (dict): Dridha/Adridha analysis
            rnanubandhan_ledger (dict): Rnanubandhan ledger
            
        Returns:
            float: Guidance score (0-100)
        """
        score = 50  # Base score
        
        # Adjust based on net karma
        net_karma = calculate_net_karma(user_doc)
        if net_karma > 100:
            score += 20
        elif net_karma > 50:
            score += 10
        elif net_karma < -50:
            score -= 20
        elif net_karma < 0:
            score -= 10
            
        # Adjust based on Dridha/Adridha ratio
        if da_analysis["dridha_ratio"] > 0.7:
            score += 15  # Stable patterns make guidance more effective
        elif da_analysis["adridha_ratio"] > 0.7:
            score -= 10  # Volatile patterns make guidance less effective
            
        # Adjust based on Rnanubandhan debt
        if rnanubandhan_ledger["total_debt"] > 50:
            score -= 15  # High debt makes progress harder
        elif rnanubandhan_ledger["total_debt"] > 20:
            score -= 5
            
        # Clamp score between 0 and 100
        return max(0, min(100, score))
    
    def _suggest_next_actions(self, user_doc: Dict, predictions: List[Dict]) -> List[Dict]:
        """
        Suggest next actions based on predictions.
        
        Args:
            user_doc (dict): User document
            predictions (list): List of predictions
            
        Returns:
            list: Suggested actions
        """
        suggestions = []
        
        # Get current balances
        balances = user_doc.get("balances", {})
        dharma_points = balances.get("DharmaPoints", 0)
        seva_points = balances.get("SevaPoints", 0)
        punya_tokens = balances.get("PunyaTokens", 0)
        
        # Always suggest basic practices
        suggestions.append({
            "action": "daily_reflection",
            "priority": "high",
            "description": "Daily self-reflection on actions and intentions",
            "benefit": "Builds self-awareness and mindfulness"
        })
        
        # Suggest based on current state
        for prediction in predictions:
            if prediction["type"] == "improvement_needed":
                suggestions.append({
                    "action": "atonement_practice",
                    "priority": "high",
                    "description": "Complete atonement for recent negative actions",
                    "benefit": "Reduces karmic debt and improves spiritual state"
                })
            elif prediction["type"] == "volatile_patterns":
                suggestions.append({
                    "action": "consistent_meditation",
                    "priority": "medium",
                    "description": "Establish a regular meditation practice",
                    "benefit": "Builds stable karma patterns"
                })
            elif prediction["type"] == "karmic_debt":
                suggestions.append({
                    "action": "service_to_others",
                    "priority": "high",
                    "description": "Engage in selfless service (Seva)",
                    "benefit": "Generates positive karma to offset debt"
                })
        
        # Suggest based on low balances
        if dharma_points < 20:
            suggestions.append({
                "action": "study_sacred_texts",
                "priority": "medium",
                "description": "Study dharmic principles and wisdom texts",
                "benefit": "Increases DharmaPoints and spiritual understanding"
            })
            
        if seva_points < 15:
            suggestions.append({
                "action": "help_others",
                "priority": "medium",
                "description": "Help others in your community or workplace",
                "benefit": "Generates SevaPoints through selfless service"
            })
            
        if punya_tokens < 10:
            suggestions.append({
                "action": "charitable_giving",
                "priority": "low",
                "description": "Make charitable donations or contributions",
                "benefit": "Generates PunyaTokens through virtuous acts"
            })
        
        return suggestions

# Global instance
karmic_predictor = KarmicPredictor()

# Convenience functions
def get_rnanubandhan_ledger(user_doc: Dict) -> Dict[str, Any]:
    """Get the complete Rnanubandhan ledger for a user."""
    return karmic_predictor.get_rnanubandhan_ledger(user_doc)

def simulate_karma_cycle(user_doc: Dict) -> Dict[str, Any]:
    """Simulate the karma cycle: Sanchita → Prarabdha → Agami."""
    return karmic_predictor.simulate_karma_cycle(user_doc)

def analyze_dridha_adridha_influence(user_doc: Dict) -> Dict[str, Any]:
    """Analyze the influence of Dridha/Adridha scoring on predictive guidance."""
    return karmic_predictor.analyze_dridha_adridha_influence(user_doc)

def predict_behavioral_trends(user_doc: Dict, action_history = None) -> Dict[str, Any]:
    """Predict behavioral trends based on karma patterns."""
    return karmic_predictor.predict_behavioral_trends(user_doc, action_history)