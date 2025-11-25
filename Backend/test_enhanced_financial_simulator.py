"""
Test script for enhanced Financial Simulator with karmic score analysis
"""
import requests
import json
from datetime import datetime

def test_enhanced_financial_simulator():
    """Test the enhanced financial simulator with karmic score functionality"""
    
    print("="*60)
    print("🧪 TESTING ENHANCED FINANCIAL SIMULATOR")
    print("="*60)
    
    # Test data for financial simulation
    financial_profile = {
        "name": "Test User",
        "monthly_income": 50000,
        "expenses": [
            {"name": "Rent", "amount": 15000},
            {"name": "Food", "amount": 8000},
            {"name": "Transportation", "amount": 5000},
            {"name": "Utilities", "amount": 3000}
        ],
        "financial_goal": "Build emergency fund and start investing",
        "financial_type": "Moderate",
        "risk_level": "medium"
    }
    
    simulation_request = {
        "profile": financial_profile,
        "simulation_months": 12,
        "user_id": "test-user"
    }
    
    try:
        print("Testing Financial Simulator (Port 8002)...")
        print(f"Request: {json.dumps(simulation_request, indent=2)}")
        
        response = requests.post(
            "http://localhost:8002/start-simulation",
            json=simulation_request,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Enhanced Financial Simulation Success!")
            print("\n📊 KARMIC SCORE ANALYSIS:")
            
            results = data.get("results", {})
            karmic_analysis = results.get("karmic_analysis", {})
            
            if karmic_analysis:
                print(f"   Overall Score: {karmic_analysis.get('overall_score', 'N/A')}/100")
                print(f"   Level: {karmic_analysis.get('level', 'N/A')}")
                print(f"   Message: {karmic_analysis.get('message', 'N/A')}")
                
                breakdown = karmic_analysis.get('breakdown', {})
                print(f"   📈 Goal Alignment: {breakdown.get('goal_alignment', 'N/A')}")
                print(f"   💪 Discipline Score: {breakdown.get('discipline_score', 'N/A')}")
                print(f"   🧘 Wellness Score: {breakdown.get('wellness_score', 'N/A')}")
                
                insights = karmic_analysis.get('insights', {})
                print(f"   💰 Savings Rate: {insights.get('savings_rate_category', 'N/A')}")
                print(f"   😰 Stress Level: {insights.get('stress_level', 'N/A')}")
                print(f"   🎯 Goal Clarity: {insights.get('goal_clarity', 'N/A')}")
            
            print("\n📅 MONTHLY DATA ANALYSIS:")
            simulation_data = results.get("simulation_data", {})
            monthly_breakdown = simulation_data.get("monthly_breakdown", [])
            
            if monthly_breakdown:
                print(f"   Total Months: {len(monthly_breakdown)}")
                print(f"   Monthly Savings: ₹{simulation_data.get('monthly_savings', 0):,.2f}")
                print(f"   Final Balance: ₹{simulation_data.get('final_balance', 0):,.2f}")
                
                # Show first 3 months as sample
                print("   📊 Sample Monthly Breakdown (First 3 months):")
                for month_data in monthly_breakdown[:3]:
                    print(f"      Month {month_data.get('month', 0)}: Balance ₹{month_data.get('balance', 0):,.2f}, Growth ₹{month_data.get('growth_this_month', 0):,.2f}")
                
                summary_metrics = simulation_data.get("summary_metrics", {})
                print(f"   📈 Average Monthly Growth: ₹{summary_metrics.get('average_monthly_growth', 0):,.2f}")
                print(f"   🚀 Compound Effect: {summary_metrics.get('compound_effect', 0):.2f}%")
            
            print("\n💡 WELLNESS INSIGHTS:")
            wellness_insights = results.get("wellness_insights", {})
            if wellness_insights:
                print(f"   Financial Stress: {wellness_insights.get('financial_stress_level', 'N/A')}")
                print(f"   Discipline Rating: {wellness_insights.get('discipline_rating', 'N/A')}")
                print(f"   Overall Wellness: {wellness_insights.get('overall_wellness', 'N/A')}")
            
            print("\n🎯 RECOMMENDATIONS:")
            recommendations = data.get("recommendations", [])
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"   {i}. {rec}")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Financial Simulator may not be running on port 8002")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_agent_simulation_fix():
    """Test the fixed agent simulation endpoint"""
    
    print("\n" + "="*60)
    print("🤖 TESTING AGENT SIMULATION FIX")
    print("="*60)
    
    # Test data for agent simulation (with additional fields)
    agent_request = {
        "agentId": "educational",
        "userId": "test-user",
        "financialProfile": {
            "name": "Test User",
            "monthly_income": 50000,
            "financial_goal": "Save for education"
        },
        "eduMentorProfile": {
            "selectedSubject": "Mathematics",
            "topic": "Algebra"
        }
    }
    
    try:
        print("Testing Agent Simulation (Port 8005)...")
        print(f"Request: {json.dumps(agent_request, indent=2)}")
        
        # Test with the enhanced API payload
        response = requests.post(
            "http://localhost:8005/start_agent_simulation",
            json={
                "agent_id": agent_request["agentId"],
                "user_id": agent_request["userId"],
                "timestamp": datetime.now().isoformat(),
                "financial_profile": agent_request.get("financialProfile"),
                "edu_mentor_profile": agent_request.get("eduMentorProfile")
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Agent Simulation Fix Success!")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Agent ID: {data.get('agent_id', 'N/A')}")
            print(f"   User ID: {data.get('user_id', 'N/A')}")
            
            # Test getting agent outputs
            output_response = requests.get("http://localhost:8005/get_agent_output", timeout=10)
            if output_response.status_code == 200:
                output_data = output_response.json()
                print(f"   📤 Agent Outputs: {output_data.get('count', 0)} messages")
                
        elif response.status_code == 422:
            print("❌ 422 Validation Error:")
            try:
                error_data = response.json()
                print(f"   Details: {json.dumps(error_data, indent=4)}")
            except:
                print(f"   Raw response: {response.text}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Subject Generation service may not be running on port 8005")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("🚀 STARTING COMPREHENSIVE TESTING")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test enhanced financial simulator
    test_enhanced_financial_simulator()
    
    # Test agent simulation fix
    test_agent_simulation_fix()
    
    print("\n" + "="*60)
    print("✅ TESTING COMPLETED")
    print("="*60)
    print("\n📋 SUMMARY:")
    print("1. Enhanced Financial Simulator now includes:")
    print("   - ✨ Karmic score analysis with detailed breakdown")
    print("   - 📊 Comprehensive monthly data tracking")
    print("   - 🏆 Milestone tracking and progress indicators")
    print("   - 💡 Wellness insights and stress level analysis")
    print("   - 🎯 Enhanced goal alignment scoring")
    print("")
    print("2. Agent Simulation endpoint now supports:")
    print("   - ✅ Additional profile data (financial, educational)")
    print("   - 🔧 Flexible Pydantic model validation")
    print("   - 📝 Enhanced logging and state management")
    print("")
    print("🔄 Next steps:")
    print("1. Restart the services to apply all changes")
    print("2. Test the frontend to see the enhanced data display")
    print("3. Verify that 422 errors are resolved")

if __name__ == "__main__":
    main()