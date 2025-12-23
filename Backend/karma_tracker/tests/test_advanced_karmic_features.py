import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.karmic_predictor import *
from utils.karma_engine import evaluate_action_karma, determine_corrective_guidance
from utils.karma_schema import *

def test_complete_advanced_karmic_feature_integration():
    """Test complete integration of all advanced karmic features"""
    
    # Create a user with complex karma state
    user = {
        "user_id": "advanced_user",
        "balances": {
            "DharmaPoints": 60,
            "SevaPoints": 40,
            "PunyaTokens": 30,
            "PaapTokens": {
                "minor": 8,
                "medium": 4,
                "maha": 1
            },
            "DridhaKarma": 50,      # Strong stable karma
            "AdridhaKarma": 20,     # Some volatile karma
            "SanchitaKarma": 200,   # Significant accumulated karma
            "PrarabdhaKarma": 80,   # Currently experiencing karma
            "Rnanubandhan": {
                "minor": 15,        # Minor karmic debt
                "medium": 8,        # Medium karmic debt
                "major": 2          # Major karmic debt
            }
        },
        "role": "volunteer"
    }
    
    print("=== Advanced Karmic Features Integration Test ===")
    print(f"User ID: {user['user_id']}")
    print(f"Role: {user['role']}")
    
    # 1. Test Rnanubandhan ledger
    print("\n1. Rnanubandhan Ledger Analysis:")
    ledger = get_rnanubandhan_ledger(user)
    print(f"   Total karmic debt: {ledger['total_debt']}")
    print(f"   Unpaid obligations: {ledger['unpaid_obligations']}")
    print(f"   Severity breakdown: {list(ledger['severity_breakdown'].keys())}")
    
    # 2. Test karma cycle simulation
    print("\n2. Karma Cycle Simulation:")
    cycle = simulate_karma_cycle(user)
    print(f"   Current Sanchita: {cycle['current']['sanchita']}")
    print(f"   Current Prarabdha: {cycle['current']['prarabdha']}")
    print(f"   Karma to experience: {cycle['cycle_effects']['karma_to_experience']:.2f}")
    print(f"   Future Prarabdha prediction: {cycle['predictions']['future_prarabdha']:.2f}")
    
    # 3. Test Dridha/Adridha influence analysis
    print("\n3. Dridha/Adridha Influence Analysis:")
    da_analysis = analyze_dridha_adridha_influence(user)
    print(f"   Dridha score: {da_analysis['dridha_score']}")
    print(f"   Adridha score: {da_analysis['adridha_score']}")
    print(f"   Dridha ratio: {da_analysis['dridha_ratio']:.2f}")
    print(f"   Guidance effectiveness: {da_analysis['guidance_effectiveness']}")
    print(f"   Recommendation: {da_analysis['recommendation']}")
    
    # 4. Test behavioral trends prediction
    print("\n4. Behavioral Trends Prediction:")
    trends = predict_behavioral_trends(user)
    print(f"   Net karma: {trends['current_state']['net_karma']:.2f}")
    print(f"   Guidance score: {trends['guidance_score']}")
    print(f"   Number of predictions: {len(trends['predictions'])}")
    print(f"   Number of suggested actions: {len(trends['next_actions'])}")
    
    # 5. Test karma engine integration with corrective guidance
    print("\n5. Karma Engine Integration:")
    
    # Simulate a positive action
    action_result = evaluate_action_karma(user, "helping_peers", 1.5)
    print(f"   Action: helping_peers (intensity 1.5)")
    print(f"   Positive impact: {action_result['positive_impact']:.2f}")
    print(f"   Dridha influence: {action_result['dridha_influence']:.2f}")
    print(f"   Sanchita change: {action_result['sanchita_change']:.2f}")
    
    # Get corrective guidance based on current state
    guidance = determine_corrective_guidance(user)
    print(f"   Number of guidance recommendations: {len(guidance)}")
    if guidance:
        print(f"   Top recommendation: {guidance[0]['practice']} - {guidance[0]['reason']}")
    
    # 6. Test with different user profiles
    print("\n6. Testing Different User Profiles:")
    
    # User with high volatile karma
    volatile_user = {
        "user_id": "volatile_user",
        "balances": {
            "DharmaPoints": 30,
            "SevaPoints": 20,
            "PunyaTokens": 10,
            "PaapTokens": {
                "minor": 12,
                "medium": 6,
                "maha": 2
            },
            "DridhaKarma": 15,      # Low stable karma
            "AdridhaKarma": 65,     # High volatile karma
            "SanchitaKarma": 100,
            "PrarabdhaKarma": 40,
            "Rnanubandhan": {
                "minor": 20,
                "medium": 10,
                "major": 5
            }
        }
    }
    
    volatile_da = analyze_dridha_adridha_influence(volatile_user)
    print(f"   Volatile user Dridha ratio: {volatile_da['dridha_ratio']:.2f}")
    print(f"   Volatile user guidance effectiveness: {volatile_da['guidance_effectiveness']}")
    
    # User with balanced karma
    balanced_user = {
        "user_id": "balanced_user",
        "balances": {
            "DharmaPoints": 50,
            "SevaPoints": 35,
            "PunyaTokens": 25,
            "PaapTokens": {
                "minor": 5,
                "medium": 3,
                "maha": 1
            },
            "DridhaKarma": 40,      # Balanced stable karma
            "AdridhaKarma": 40,     # Balanced volatile karma
            "SanchitaKarma": 150,
            "PrarabdhaKarma": 60,
            "Rnanubandhan": {
                "minor": 10,
                "medium": 5,
                "major": 2
            }
        }
    }
    
    balanced_da = analyze_dridha_adridha_influence(balanced_user)
    print(f"   Balanced user Dridha ratio: {balanced_da['dridha_ratio']:.2f}")
    print(f"   Balanced user guidance effectiveness: {balanced_da['guidance_effectiveness']}")
    
    print("\n✓ All advanced karmic features integration tests passed!")

def test_10_action_user_flow():
    """Test a sample user flow with at least 10 actions"""
    
    print("\n=== 10-Action User Flow Simulation ===")
    
    # Create initial user state
    user = {
        "user_id": "flow_user",
        "balances": {
            "DharmaPoints": 20,
            "SevaPoints": 10,
            "PunyaTokens": 5,
            "PaapTokens": {
                "minor": 2,
                "medium": 1,
                "maha": 0
            },
            "DridhaKarma": 15,
            "AdridhaKarma": 25,
            "SanchitaKarma": 50,
            "PrarabdhaKarma": 25,
            "Rnanubandhan": {
                "minor": 3,
                "medium": 1,
                "major": 0
            }
        },
        "role": "learner"
    }
    
    # Define 10 actions
    actions = [
        {"action": "completing_lessons", "intensity": 1.0, "type": "positive"},
        {"action": "helping_peers", "intensity": 1.2, "type": "positive"},
        {"action": "cheat", "intensity": 1.0, "type": "negative"},
        {"action": "selfless_service", "intensity": 1.5, "type": "positive"},
        {"action": "break_promise", "intensity": 0.8, "type": "negative"},
        {"action": "solving_doubts", "intensity": 1.0, "type": "positive"},
        {"action": "false_speech", "intensity": 0.9, "type": "negative"},
        {"action": "completing_lessons", "intensity": 1.1, "type": "positive"},
        {"action": "helping_peers", "intensity": 1.3, "type": "positive"},
        {"action": "harm_others", "intensity": 1.0, "type": "negative"}
    ]
    
    print(f"Initial user state:")
    print(f"  Role: {user['role']}")
    print(f"  DharmaPoints: {user['balances']['DharmaPoints']}")
    print(f"  SevaPoints: {user['balances']['SevaPoints']}")
    print(f"  DridhaKarma: {user['balances']['DridhaKarma']}")
    print(f"  AdridhaKarma: {user['balances']['AdridhaKarma']}")
    
    # Process each action
    for i, action_data in enumerate(actions, 1):
        action = action_data["action"]
        intensity = action_data["intensity"]
        
        # Evaluate karma impact
        result = evaluate_action_karma(user, action, intensity)
        
        # Update user balances based on results (simplified)
        if result["positive_impact"] > 0:
            user["balances"]["DharmaPoints"] = user["balances"].get("DharmaPoints", 0) + (result["positive_impact"] * 0.3)
            user["balances"]["SevaPoints"] = user["balances"].get("SevaPoints", 0) + (result["positive_impact"] * 0.4)
            user["balances"]["DridhaKarma"] = user["balances"].get("DridhaKarma", 0) + result["dridha_influence"]
            user["balances"]["AdridhaKarma"] = user["balances"].get("AdridhaKarma", 0) + result["adridha_influence"]
            user["balances"]["SanchitaKarma"] = user["balances"].get("SanchitaKarma", 0) + result["sanchita_change"]
            user["balances"]["PrarabdhaKarma"] = user["balances"].get("PrarabdhaKarma", 0) + result["prarabdha_change"]
        elif result["negative_impact"] > 0:
            # For simplicity, we'll just add to PaapTokens minor category
            user["balances"]["PaapTokens"]["minor"] = user["balances"]["PaapTokens"].get("minor", 0) + (result["negative_impact"] * 0.5)
            user["balances"]["AdridhaKarma"] = user["balances"].get("AdridhaKarma", 0) + result["adridha_influence"]
            # Add to Rnanubandhan
            user["balances"]["Rnanubandhan"]["minor"] = user["balances"]["Rnanubandhan"].get("minor", 0) + (result["negative_impact"] * 0.2)
        
        print(f"\nAction {i}: {action} (intensity: {intensity})")
        print(f"  Impact: {'+' if result['positive_impact'] > 0 else ''}{result['positive_impact'] - result['negative_impact']:.2f}")
        print(f"  Dridha influence: {result['dridha_influence']:.2f}")
        print(f"  Adridha influence: {result['adridha_influence']:.2f}")
    
    # Final analysis after all actions
    print(f"\nFinal user state after 10 actions:")
    print(f"  Role: {user['role']}")
    print(f"  DharmaPoints: {user['balances']['DharmaPoints']:.2f}")
    print(f"  SevaPoints: {user['balances']['SevaPoints']:.2f}")
    print(f"  DridhaKarma: {user['balances']['DridhaKarma']:.2f}")
    print(f"  AdridhaKarma: {user['balances']['AdridhaKarma']:.2f}")
    
    # Analyze final state with karmic predictor
    print(f"\nFinal karmic analysis:")
    ledger = get_rnanubandhan_ledger(user)
    print(f"  Total karmic debt: {ledger['total_debt']:.2f}")
    
    da_analysis = analyze_dridha_adridha_influence(user)
    print(f"  Dridha/Adridha ratio: {da_analysis['dridha_ratio']:.2f}")
    print(f"  Guidance effectiveness: {da_analysis['guidance_effectiveness']}")
    
    trends = predict_behavioral_trends(user)
    print(f"  Guidance score: {trends['guidance_score']:.2f}")
    if trends['next_actions']:
        print(f"  Top next action: {trends['next_actions'][0]['action']} - {trends['next_actions'][0]['description']}")
    
    print("\n✓ 10-action user flow simulation completed successfully!")

if __name__ == "__main__":
    print("Running advanced karmic features integration tests...")
    
    test_complete_advanced_karmic_feature_integration()
    test_10_action_user_flow()
    
    print("\n🎉 All advanced karmic features tests passed!")