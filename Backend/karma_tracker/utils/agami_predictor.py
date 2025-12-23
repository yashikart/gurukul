"""
Agami Karma Predictor Module

This module implements the Agami Karma (future karma) prediction system.
Agami Karma represents the karmic results that are queued to manifest in the future.
"""

import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from database import users_col, qtable_col
from utils.karma_schema import get_karma_weights, calculate_weighted_karma_score
from utils.loka import calculate_net_karma
from utils.paap import get_total_paap_score
from utils.merit import compute_user_merit_score, determine_role_from_merit
from utils.karmic_predictor import karmic_predictor
from config import ACTIONS, ROLE_SEQUENCE, REWARD_MAP, ALPHA, GAMMA
import json
import os

class AgamiKarmaPredictor:
    """Predicts future karmic outcomes based on current actions and Q-learning weights"""
    
    def __init__(self):
        """Initialize the Agami Karma predictor"""
        self.context_weights_file = "context_weights.json"
        self.context_weights = self._load_context_weights()
    
    def _load_context_weights(self) -> Dict:
        """Load context-sensitive Purushartha weights"""
        if os.path.exists(self.context_weights_file):
            try:
                with open(self.context_weights_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load context weights: {e}")
                return {}
        return {}
    
    def _save_context_weights(self):
        """Save context weights to file"""
        try:
            with open(self.context_weights_file, 'w') as f:
                json.dump(self.context_weights, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save context weights: {e}")
    
    def predict_agami_karma(self, user_id: str, scenario: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Predict likely karmic outcomes for a user based on current Q-learning weights.
        
        Args:
            user_id (str): The user's ID
            scenario (dict, optional): Specific scenario to predict for
            
        Returns:
            dict: Agami karma prediction
        """
        # Get user document
        user_doc = users_col.find_one({"user_id": user_id})
        if not user_doc:
            raise ValueError(f"User {user_id} not found")
        
        # Get current karma state
        current_state = self._get_current_karma_state(user_doc)
        
        # Get Q-table
        q_table = self._get_q_table()
        
        # Predict future karma based on Q-learning weights
        predictions = self._predict_from_q_table(user_doc, q_table, scenario)
        
        # Calculate Agami karma (future karma) based on current trajectory
        agami_karma = self._calculate_agami_karma(user_doc, predictions)
        
        # Get context-aware predictions if context is provided
        context_predictions = {}
        if scenario and scenario.get("context"):
            context_predictions = self._get_context_aware_predictions(user_doc, scenario)
        
        return {
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_state": current_state,
            "q_learning_predictions": predictions,
            "agami_karma": agami_karma,
            "context_aware_predictions": context_predictions,
            "recommendations": self._generate_recommendations(user_doc, predictions, agami_karma)
        }
    
    def _get_current_karma_state(self, user_doc: Dict) -> Dict[str, Any]:
        """Get the current karma state for a user"""
        return {
            "net_karma": calculate_net_karma(user_doc),
            "merit_score": compute_user_merit_score(user_doc),
            "paap_score": get_total_paap_score(user_doc),
            "weighted_karma": calculate_weighted_karma_score(user_doc),
            "role": user_doc.get("role", "learner"),
            "balances": user_doc.get("balances", {})
        }
    
    def _get_q_table(self) -> np.ndarray:
        """Get the current Q-table from database"""
        q_doc = qtable_col.find_one({})
        if q_doc and "q" in q_doc:
            try:
                return np.array(q_doc["q"])
            except Exception:
                pass
        # Return empty Q-table if none found
        n_states = len(ROLE_SEQUENCE)
        n_actions = len(ACTIONS)
        return np.zeros((n_states, n_actions))
    
    def _predict_from_q_table(self, user_doc: Dict, q_table: np.ndarray, scenario: Optional[Dict] = None) -> Dict[str, Any]:
        """Predict future outcomes based on Q-learning weights"""
        user_role = user_doc.get("role", "learner")
        if user_role not in ROLE_SEQUENCE:
            user_role = "learner"
        
        role_index = ROLE_SEQUENCE.index(user_role)
        
        # Get Q-values for current role
        if role_index < q_table.shape[0]:
            role_q_values = q_table[role_index]
        else:
            role_q_values = np.zeros(len(ACTIONS))
        
        # Rank actions by Q-value
        action_rankings = []
        for i, action in enumerate(ACTIONS):
            if i < len(role_q_values):
                q_value = role_q_values[i]
                expected_reward = self._get_expected_reward(action)
                action_rankings.append({
                    "action": action,
                    "q_value": float(q_value),
                    "expected_reward": expected_reward,
                    "predicted_role_impact": self._predict_role_impact(user_doc, action, expected_reward)
                })
        
        # Sort by Q-value (descending)
        action_rankings.sort(key=lambda x: x["q_value"], reverse=True)
        
        return {
            "best_actions": action_rankings[:5],  # Top 5 actions
            "worst_actions": action_rankings[-5:],  # Bottom 5 actions
            "role_progression": self._predict_role_progression(user_doc, action_rankings),
            "confidence": self._calculate_prediction_confidence(q_table)
        }
    
    def _get_expected_reward(self, action: str) -> float:
        """Get expected reward for an action"""
        if action in REWARD_MAP:
            return float(REWARD_MAP[action]["value"])
        return 0.0
    
    def _predict_role_impact(self, user_doc: Dict, action: str, reward: float) -> Dict[str, Any]:
        """Predict how an action will impact user role"""
        current_merit = compute_user_merit_score(user_doc)
        current_role = user_doc.get("role", "learner")
        
        # Simulate the reward impact
        temp_balances = user_doc.get("balances", {}).copy()
        
        if action in REWARD_MAP:
            token = REWARD_MAP[action]["token"]
            if token in temp_balances:
                temp_balances[token] = temp_balances.get(token, 0) + reward
            else:
                temp_balances[token] = reward
        
        # Calculate new merit score
        new_merit = (
            temp_balances.get("DharmaPoints", 0) * 1.0 + 
            temp_balances.get("SevaPoints", 0) * 1.2 + 
            temp_balances.get("PunyaTokens", 0) * 3.0
        )
        
        new_role = determine_role_from_merit(new_merit)
        
        return {
            "current_merit": current_merit,
            "new_merit": new_merit,
            "merit_change": new_merit - current_merit,
            "current_role": current_role,
            "predicted_role": new_role,
            "role_change": new_role != current_role
        }
    
    def _predict_role_progression(self, user_doc: Dict, action_rankings: List[Dict]) -> List[Dict]:
        """Predict role progression based on top actions"""
        progression = []
        current_role = user_doc.get("role", "learner")
        
        # Look at top positive actions
        positive_actions = [a for a in action_rankings if a["q_value"] > 0][:3]
        
        for action_info in positive_actions:
            action = action_info["action"]
            reward = action_info["expected_reward"]
            
            impact = self._predict_role_impact(user_doc, action, reward)
            if impact["role_change"]:
                progression.append({
                    "action": action,
                    "from_role": current_role,
                    "to_role": impact["predicted_role"],
                    "merit_gain": impact["merit_change"]
                })
        
        return progression
    
    def _calculate_prediction_confidence(self, q_table: np.ndarray) -> float:
        """Calculate confidence in predictions based on Q-table quality"""
        if q_table.size == 0:
            return 0.0
        
        # Confidence based on how much of the Q-table has been explored
        non_zero_count = np.count_nonzero(q_table)
        total_count = q_table.size
        
        if total_count == 0:
            return 0.0
            
        exploration_ratio = non_zero_count / total_count
        
        # Confidence increases with exploration but caps at 90%
        return min(0.9, exploration_ratio * 2)
    
    def _calculate_agami_karma(self, user_doc: Dict, predictions: Dict) -> Dict[str, Any]:
        """Calculate future karma based on current trajectory"""
        current_state = self._get_current_karma_state(user_doc)
        
        # Get top recommended actions
        best_actions = predictions.get("best_actions", [])
        
        # Simulate karma changes from top actions
        projected_balances = user_doc.get("balances", {}).copy()
        total_projected_change = 0
        
        for action_info in best_actions[:3]:  # Top 3 actions
            action = action_info["action"]
            reward = action_info["expected_reward"]
            
            if action in REWARD_MAP:
                token = REWARD_MAP[action]["token"]
                projected_balances[token] = projected_balances.get(token, 0) + reward
                total_projected_change += reward
        
        # Calculate projected karma scores
        projected_merit = (
            projected_balances.get("DharmaPoints", 0) * 1.0 + 
            projected_balances.get("SevaPoints", 0) * 1.2 + 
            projected_balances.get("PunyaTokens", 0) * 3.0
        )
        
        # Project Paap changes (simplified)
        current_paap = get_total_paap_score(user_doc)
        projected_paap = max(0, current_paap * 0.9)  # Natural decay
        
        projected_net_karma = projected_merit - projected_paap
        
        return {
            "projected_balances": projected_balances,
            "projected_merit_score": projected_merit,
            "projected_paap_score": projected_paap,
            "projected_net_karma": projected_net_karma,
            "projected_role": determine_role_from_merit(projected_merit),
            "expected_change": projected_net_karma - current_state["net_karma"],
            "time_horizon": "30_days"
        }
    
    def _get_context_aware_predictions(self, user_doc: Dict, scenario: Dict) -> Dict[str, Any]:
        """Get predictions based on context (time, role, goals)"""
        context = scenario.get("context", {})
        user_role = user_doc.get("role", "learner")
        
        # Get context weights
        context_key = f"{user_role}_{context.get('environment', 'default')}"
        weights = self.context_weights.get(context_key, {})
        
        # Apply context weights to Purushartha categories
        purushartha_modifiers = {
            "Dharma": weights.get("dharma_weight", 1.0),
            "Artha": weights.get("artha_weight", 1.0),
            "Kama": weights.get("kama_weight", 1.0),
            "Moksha": weights.get("moksha_weight", 1.0)
        }
        
        # Adjust action rankings based on context
        adjusted_predictions = {}
        
        # For example, in Gurukul environment, Artha actions might be weighted differently
        if context.get("environment") == "gurukul":
            adjusted_predictions["environment_adjustment"] = "In Gurukul, Artha actions are weighted for learning context"
            purushartha_modifiers["Artha"] *= 1.2  # Learning-focused Artha
        elif context.get("environment") == "game_realm":
            adjusted_predictions["environment_adjustment"] = "In Game Realm, Kama actions are weighted for engagement"
            purushartha_modifiers["Kama"] *= 1.3  # Engagement-focused Kama
        
        return {
            "context": context,
            "purushartha_modifiers": purushartha_modifiers,
            "adjusted_predictions": adjusted_predictions
        }
    
    def _generate_recommendations(self, user_doc: Dict, predictions: Dict, agami_karma: Dict) -> List[Dict]:
        """Generate personalized recommendations based on predictions"""
        recommendations = []
        
        # Get current state
        current_state = self._get_current_karma_state(user_doc)
        
        # Recommendation 1: Based on Q-learning predictions
        best_actions = predictions.get("best_actions", [])
        if best_actions:
            top_action = best_actions[0]
            recommendations.append({
                "type": "action_recommendation",
                "priority": "high",
                "action": top_action["action"],
                "reasoning": f"High Q-value action ({top_action['q_value']:.2f}) with expected reward of {top_action['expected_reward']}",
                "expected_benefit": {
                    "merit_gain": top_action["predicted_role_impact"]["merit_change"],
                    "role_progression": top_action["predicted_role_impact"]["role_change"]
                }
            })
        
        # Recommendation 2: Based on Agami karma projection
        expected_change = agami_karma.get("expected_change", 0)
        if expected_change > 10:
            recommendations.append({
                "type": "trajectory_confirmation",
                "priority": "medium",
                "action": "continue_current_path",
                "reasoning": f"Positive karma trajectory predicted (+{expected_change:.1f} over 30 days)",
                "expected_benefit": {
                    "net_karma_improvement": expected_change,
                    "role_advancement": agami_karma["projected_role"] != current_state["role"]
                }
            })
        elif expected_change < -5:
            recommendations.append({
                "type": "course_correction",
                "priority": "high",
                "action": "focus_on_atonement",
                "reasoning": f"Negative karma trajectory predicted ({expected_change:.1f} over 30 days)",
                "expected_benefit": {
                    "karmic_debt_reduction": "significant"
                }
            })
        
        # Recommendation 3: Based on role progression
        role_progression = predictions.get("role_progression", [])
        if role_progression:
            next_role_action = role_progression[0]
            recommendations.append({
                "type": "role_advancement",
                "priority": "high",
                "action": next_role_action["action"],
                "reasoning": f"Action leads to role advancement from {next_role_action['from_role']} to {next_role_action['to_role']}",
                "expected_benefit": {
                    "merit_gain": next_role_action["merit_gain"],
                    "new_role": next_role_action["to_role"]
                }
            })
        
        return recommendations
    
    def update_context_weights(self, context_key: str, weights: Dict):
        """Update context-sensitive weights"""
        self.context_weights[context_key] = weights
        self._save_context_weights()
    
    def get_context_weights(self, context_key: str) -> Dict:
        """Get context-sensitive weights"""
        return self.context_weights.get(context_key, {})

# Global instance
agami_predictor = AgamiKarmaPredictor()

# Convenience function
def predict_agami_karma(user_id: str, scenario: Optional[Dict] = None) -> Dict[str, Any]:
    """Predict Agami (future) karma for a user"""
    return agami_predictor.predict_agami_karma(user_id, scenario)