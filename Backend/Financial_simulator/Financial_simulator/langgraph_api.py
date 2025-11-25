"""
Financial Simulator API using LangGraph
Provides financial forecasting, simulation, and analysis capabilities
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
import asyncio
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.append(str(backend_dir))

try:
    # Try to import advanced forecasting from orchestration
    orchestration_dir = backend_dir / "orchestration" / "unified_orchestration_system"
    sys.path.append(str(orchestration_dir))
    
    from enhanced_prophet_model import EnhancedProphetModel
    from enhanced_arima_model import EnhancedARIMAModel
    from smart_model_selector import SmartModelSelector
    ADVANCED_FORECASTING = True
    logger.info("Advanced forecasting models loaded successfully")
except ImportError as e:
    ADVANCED_FORECASTING = False
    logger.warning(f"Advanced forecasting not available: {e}")

# Pydantic models
class FinancialProfile(BaseModel):
    """Financial profile for simulation"""
    name: str
    monthly_income: float = Field(gt=0, description="Monthly income in currency units")
    expenses: List[Dict[str, Any]] = Field(default_factory=list, description="List of expenses")
    financial_goal: str = Field(description="Financial goal description")
    financial_type: str = Field(default="Conservative", description="Investment style: Conservative, Moderate, Aggressive")
    risk_level: str = Field(default="Low", description="Risk tolerance: Low, Medium, High")

class SimulationRequest(BaseModel):
    """Request for financial simulation"""
    profile: FinancialProfile
    simulation_months: int = Field(12, ge=1, le=120, description="Number of months to simulate")
    user_id: Optional[str] = Field(None, description="User ID for tracking")

class MarketData(BaseModel):
    """Market data for forecasting"""
    symbol: str = Field(description="Financial symbol or identifier")
    data: List[Dict[str, Any]] = Field(description="Historical data points")
    forecast_periods: int = Field(30, ge=1, le=365, description="Number of periods to forecast")

class SimulationResponse(BaseModel):
    """Response from financial simulation"""
    status: str
    simulation_id: str
    results: Dict[str, Any]
    recommendations: List[str]
    timestamp: str

class ForecastResponse(BaseModel):
    """Response from financial forecasting"""
    status: str
    forecast_data: List[Dict[str, Any]]
    model_used: str
    accuracy_metrics: Dict[str, float]
    summary: Dict[str, Any]
    timestamp: str

# FastAPI app
app = FastAPI(
    title="Financial Simulator API",
    description="Financial forecasting, simulation, and analysis using LangGraph",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FinancialSimulator:
    """Main financial simulator class with enhanced agent-based functionality"""
    
    def __init__(self):
        self.active_simulations = {}
        self.simulation_results = {}
        
    def calculate_savings_potential(self, profile: FinancialProfile) -> Dict[str, float]:
        """Calculate savings potential based on profile"""
        total_expenses = sum(float(expense.get('amount', 0)) for expense in profile.expenses)
        potential_savings = profile.monthly_income - total_expenses
        
        return {
            "monthly_income": profile.monthly_income,
            "total_expenses": total_expenses,
            "potential_savings": potential_savings,
            "savings_rate": (potential_savings / profile.monthly_income) * 100 if profile.monthly_income > 0 else 0
        }
    
    def calculate_karmic_score(self, profile: FinancialProfile, savings_info: Dict) -> Dict[str, Any]:
        """Calculate karmic score based on financial behavior and goals"""
        savings_rate = savings_info["savings_rate"]
        goal_alignment = 0
        discipline_score = 0
        wellness_score = 0
        
        # Goal alignment scoring (0-100)
        if "emergency" in profile.financial_goal.lower():
            goal_alignment = 85  # Emergency fund is high priority
        elif "investment" in profile.financial_goal.lower() or "growth" in profile.financial_goal.lower():
            goal_alignment = 75  # Investment goals are good
        elif "debt" in profile.financial_goal.lower() or "pay off" in profile.financial_goal.lower():
            goal_alignment = 90  # Debt reduction is excellent
        elif "save" in profile.financial_goal.lower():
            goal_alignment = 70  # General saving is good
        else:
            goal_alignment = 50  # Unclear goals
        
        # Discipline score based on savings rate
        if savings_rate >= 20:
            discipline_score = 95
        elif savings_rate >= 15:
            discipline_score = 85
        elif savings_rate >= 10:
            discipline_score = 75
        elif savings_rate >= 5:
            discipline_score = 60
        else:
            discipline_score = 30
        
        # Wellness score based on financial stress indicators
        expense_to_income_ratio = savings_info["total_expenses"] / profile.monthly_income
        if expense_to_income_ratio < 0.7:
            wellness_score = 90  # Very healthy
        elif expense_to_income_ratio < 0.8:
            wellness_score = 80  # Healthy
        elif expense_to_income_ratio < 0.9:
            wellness_score = 65  # Moderate stress
        elif expense_to_income_ratio < 0.95:
            wellness_score = 45  # High stress
        else:
            wellness_score = 25  # Very high stress
        
        # Calculate overall karmic score (weighted average)
        karmic_score = (
            goal_alignment * 0.3 +  # 30% weight
            discipline_score * 0.4 +  # 40% weight
            wellness_score * 0.3     # 30% weight
        )
        
        # Determine karmic level
        if karmic_score >= 90:
            karmic_level = "Enlightened Investor"
            karmic_message = "Your financial wisdom shines brightly! You demonstrate exceptional discipline and clarity."
        elif karmic_score >= 80:
            karmic_level = "Wise Planner"
            karmic_message = "You show great financial wisdom. Continue on this path of mindful money management."
        elif karmic_score >= 70:
            karmic_level = "Conscious Saver"
            karmic_message = "You're developing good financial habits. Keep building your financial consciousness."
        elif karmic_score >= 60:
            karmic_level = "Awakening Spender"
            karmic_message = "You're beginning to understand financial balance. Focus on increasing your savings discipline."
        else:
            karmic_level = "Seeking Balance"
            karmic_message = "Your financial journey is just beginning. Embrace mindful spending and conscious saving."
        
        return {
            "overall_score": round(karmic_score, 2),
            "level": karmic_level,
            "message": karmic_message,
            "breakdown": {
                "goal_alignment": round(goal_alignment, 2),
                "discipline_score": round(discipline_score, 2),
                "wellness_score": round(wellness_score, 2)
            },
            "insights": {
                "savings_rate_category": "Excellent" if savings_rate >= 20 else "Good" if savings_rate >= 10 else "Needs Improvement",
                "stress_level": "Low" if expense_to_income_ratio < 0.8 else "Medium" if expense_to_income_ratio < 0.9 else "High",
                "goal_clarity": "Clear" if goal_alignment >= 70 else "Moderate" if goal_alignment >= 50 else "Unclear"
            }
        }
    
    def generate_investment_recommendations(self, profile: FinancialProfile) -> List[str]:
        """Generate investment recommendations based on profile"""
        recommendations = []
        
        savings_info = self.calculate_savings_potential(profile)
        savings_rate = savings_info["savings_rate"]
        
        if savings_rate < 10:
            recommendations.append("Focus on expense reduction to increase savings rate above 10%")
            recommendations.append("Consider creating a detailed budget to track spending")
        elif savings_rate < 20:
            recommendations.append("Good savings rate! Consider diversifying into low-risk investments")
            recommendations.append("Build an emergency fund covering 3-6 months of expenses")
        else:
            recommendations.append("Excellent savings rate! You can consider higher-yield investments")
        
        # Risk-based recommendations
        if profile.risk_level.lower() == "low":
            recommendations.append("Consider government bonds, high-yield savings accounts, and CDs")
            recommendations.append("Focus on capital preservation with modest growth")
        elif profile.risk_level.lower() == "medium":
            recommendations.append("Balanced portfolio with 60% stocks, 40% bonds")
            recommendations.append("Consider index funds and diversified ETFs")
        else:  # High risk
            recommendations.append("Growth-focused portfolio with higher stock allocation")
            recommendations.append("Consider growth stocks, emerging markets, and alternative investments")
        
        return recommendations
    
    def simulate_financial_future(self, profile: FinancialProfile, months: int) -> Dict[str, Any]:
        """Simulate financial future over specified months with detailed monthly tracking"""
        savings_info = self.calculate_savings_potential(profile)
        monthly_savings = savings_info["potential_savings"]
        
        if monthly_savings <= 0:
            return {
                "status": "warning",
                "message": "Negative or zero savings potential",
                "monthly_savings": monthly_savings,
                "projected_savings": [],
                "monthly_breakdown": []
            }
        
        # Growth rate based on risk level
        annual_growth_rates = {
            "low": 0.03,    # 3% annual return
            "medium": 0.07, # 7% annual return
            "high": 0.10    # 10% annual return
        }
        
        annual_rate = annual_growth_rates.get(profile.risk_level.lower(), 0.05)
        monthly_rate = annual_rate / 12
        
        # Simulate month by month with detailed tracking
        projected_savings = []
        monthly_breakdown = []
        current_balance = 0
        
        for month in range(1, months + 1):
            # Calculate month details
            monthly_contribution = monthly_savings
            growth_this_month = current_balance * monthly_rate
            
            # Add monthly savings
            current_balance += monthly_contribution
            # Apply growth
            current_balance += growth_this_month
            
            # Calculate additional metrics for this month
            total_contributed = monthly_savings * month
            total_growth = current_balance - total_contributed
            
            # Monthly breakdown for detailed analysis
            monthly_data = {
                "month": month,
                "balance": round(current_balance, 2),
                "monthly_contribution": round(monthly_contribution, 2),
                "growth_this_month": round(growth_this_month, 2),
                "total_contributed": round(total_contributed, 2),
                "total_growth": round(total_growth, 2),
                "growth_percentage": round((total_growth / total_contributed * 100) if total_contributed > 0 else 0, 2),
                "discipline_score": self._calculate_monthly_discipline_score(month, monthly_contribution, profile),
                "milestone_reached": self._check_milestones(current_balance, total_contributed)
            }
            
            projected_savings.append({
                "month": month,
                "balance": round(current_balance, 2),
                "total_contributed": round(total_contributed, 2),
                "growth_amount": round(total_growth, 2)
            })
            
            monthly_breakdown.append(monthly_data)
        
        return {
            "status": "success",
            "monthly_savings": monthly_savings,
            "annual_growth_rate": annual_rate,
            "final_balance": projected_savings[-1]["balance"] if projected_savings else 0,
            "total_contributed": projected_savings[-1]["total_contributed"] if projected_savings else 0,
            "total_growth": projected_savings[-1]["growth_amount"] if projected_savings else 0,
            "projected_savings": projected_savings,
            "monthly_breakdown": monthly_breakdown,
            "summary_metrics": {
                "average_monthly_growth": round(sum(m["growth_this_month"] for m in monthly_breakdown) / len(monthly_breakdown), 2) if monthly_breakdown else 0,
                "compound_effect": round(((projected_savings[-1]["balance"] / projected_savings[-1]["total_contributed"]) - 1) * 100, 2) if projected_savings and projected_savings[-1]["total_contributed"] > 0 else 0,
                "best_performing_month": max(monthly_breakdown, key=lambda x: x["growth_this_month"])["month"] if monthly_breakdown else 0
            }
        }
    
    def _calculate_monthly_discipline_score(self, month: int, contribution: float, profile: FinancialProfile) -> float:
        """Calculate discipline score for a specific month"""
        expected_contribution = self.calculate_savings_potential(profile)["potential_savings"]
        if expected_contribution <= 0:
            return 50
        
        ratio = contribution / expected_contribution
        if ratio >= 1.0:
            base_score = 100
        elif ratio >= 0.8:
            base_score = 85
        elif ratio >= 0.6:
            base_score = 70
        else:
            base_score = 50
        
        # Add consistency bonus for later months
        consistency_bonus = min(month * 0.5, 10)
        return min(base_score + consistency_bonus, 100)
    
    def _check_milestones(self, current_balance: float, total_contributed: float) -> Dict[str, Any]:
        """Check if any financial milestones have been reached"""
        milestones = {
            "first_thousand": 1000,
            "emergency_fund_start": 5000,
            "investment_ready": 10000,
            "substantial_savings": 25000,
            "major_milestone": 50000
        }
        
        reached_milestones = []
        for milestone_name, amount in milestones.items():
            if current_balance >= amount:
                reached_milestones.append({
                    "name": milestone_name,
                    "amount": amount,
                    "message": self._get_milestone_message(milestone_name)
                })
        
        return {
            "reached": len(reached_milestones) > 0,
            "milestones": reached_milestones,
            "next_milestone": self._get_next_milestone(current_balance, milestones)
        }
    
    def _get_milestone_message(self, milestone_name: str) -> str:
        """Get congratulatory message for reaching a milestone"""
        messages = {
            "first_thousand": "🎉 Congratulations! You've reached your first ₹1,000 milestone!",
            "emergency_fund_start": "🛡️ Great job! You're building a solid emergency fund foundation!",
            "investment_ready": "📈 Excellent! You're ready to explore investment opportunities!",
            "substantial_savings": "💎 Outstanding! You've built substantial savings!",
            "major_milestone": "🏆 Incredible achievement! You've reached a major financial milestone!"
        }
        return messages.get(milestone_name, "🎯 Milestone achieved!")
    
    def _get_next_milestone(self, current_balance: float, milestones: Dict) -> Dict[str, Any]:
        """Get information about the next milestone to reach"""
        for milestone_name, amount in sorted(milestones.items(), key=lambda x: x[1]):
            if current_balance < amount:
                return {
                    "name": milestone_name,
                    "amount": amount,
                    "remaining": amount - current_balance,
                    "progress_percentage": round((current_balance / amount) * 100, 2)
                }
        return {
            "name": "financial_freedom",
            "amount": 100000,
            "remaining": 100000 - current_balance,
            "progress_percentage": round((current_balance / 100000) * 100, 2)
        }

# Initialize simulator
simulator = FinancialSimulator()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Financial Simulator",
        "timestamp": datetime.now().isoformat(),
        "advanced_forecasting": ADVANCED_FORECASTING
    }

@app.post("/start-simulation", response_model=SimulationResponse)
async def start_financial_simulation(request: SimulationRequest):
    """Start a financial simulation with enhanced karmic score analysis"""
    try:
        simulation_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(simulator.active_simulations)}"
        
        # Calculate savings potential
        savings_info = simulator.calculate_savings_potential(request.profile)
        
        # Calculate karmic score
        karmic_analysis = simulator.calculate_karmic_score(request.profile, savings_info)
        
        # Generate recommendations
        recommendations = simulator.generate_investment_recommendations(request.profile)
        
        # Run enhanced simulation
        simulation_results = simulator.simulate_financial_future(request.profile, request.simulation_months)
        
        # Store simulation
        simulator.active_simulations[simulation_id] = {
            "profile": request.profile.dict(),
            "created_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        # Enhanced results with karmic score and detailed monthly data
        results = {
            "simulation_id": simulation_id,
            "profile_analysis": savings_info,
            "karmic_analysis": karmic_analysis,
            "simulation_data": simulation_results,
            "investment_recommendations": recommendations,
            "goal_analysis": {
                "goal": request.profile.financial_goal,
                "achievability": "achievable" if savings_info["potential_savings"] > 0 else "challenging",
                "suggested_timeline": f"{request.simulation_months} months",
                "karmic_alignment": karmic_analysis["breakdown"]["goal_alignment"]
            },
            "wellness_insights": {
                "financial_stress_level": karmic_analysis["insights"]["stress_level"],
                "discipline_rating": karmic_analysis["insights"]["savings_rate_category"],
                "goal_clarity": karmic_analysis["insights"]["goal_clarity"],
                "overall_wellness": karmic_analysis["level"]
            },
            "monthly_insights": {
                "total_months": len(simulation_results.get("monthly_breakdown", [])),
                "best_performing_month": simulation_results.get("summary_metrics", {}).get("best_performing_month", 0),
                "average_growth": simulation_results.get("summary_metrics", {}).get("average_monthly_growth", 0),
                "compound_effect": simulation_results.get("summary_metrics", {}).get("compound_effect", 0)
            }
        }
        
        simulator.simulation_results[simulation_id] = results
        
        return SimulationResponse(
            status="success",
            simulation_id=simulation_id,
            results=results,
            recommendations=recommendations + [f"Your current karmic score is {karmic_analysis['overall_score']}/100 - {karmic_analysis['level']}"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@app.get("/simulation/{simulation_id}")
async def get_simulation_results(simulation_id: str):
    """Get results of a specific simulation"""
    if simulation_id not in simulator.simulation_results:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return {
        "status": "success",
        "simulation_id": simulation_id,
        "results": simulator.simulation_results[simulation_id],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/simulation-results/{simulation_id}")
async def get_simulation_results_by_task_id(simulation_id: str):
    """Get results of a specific simulation (alternative endpoint for frontend compatibility)"""
    if simulation_id not in simulator.simulation_results:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    # Format response to match expected frontend structure
    results = simulator.simulation_results[simulation_id]
    
    return {
        "task_id": simulation_id,
        "task_status": "completed",
        "status": "success",
        "ready": True,
        "message": "Simulation results ready",
        "user_id": "anonymous-user",
        "data": results,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/simulations")
async def list_simulations():
    """List all active simulations"""
    return {
        "status": "success",
        "simulations": list(simulator.active_simulations.keys()),
        "count": len(simulator.active_simulations),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/forecast", response_model=ForecastResponse)
async def create_financial_forecast(market_data: MarketData):
    """Create financial forecast using advanced models"""
    if not ADVANCED_FORECASTING:
        # Simple fallback forecast
        return ForecastResponse(
            status="fallback",
            forecast_data=[
                {
                    "date": (datetime.now() + timedelta(days=i)).isoformat(),
                    "predicted_value": 100 + (i * 0.5),  # Simple linear growth
                    "confidence": "low"
                }
                for i in range(1, market_data.forecast_periods + 1)
            ],
            model_used="simple_linear",
            accuracy_metrics={"note": "Advanced forecasting not available"},
            summary={"trend": "upward", "confidence": "low"},
            timestamp=datetime.now().isoformat()
        )
    
    try:
        # Use advanced forecasting if available
        df_data = []
        for point in market_data.data:
            df_data.append({
                'ds': pd.to_datetime(point.get('date')),
                'y': float(point.get('value', 0))
            })
        
        df = pd.DataFrame(df_data)
        
        if len(df) < 10:
            raise HTTPException(status_code=400, detail="Need at least 10 data points for forecasting")
        
        # Use smart model selector
        selector = SmartModelSelector("general")
        selection_result = selector.select_best_model(df)
        
        if selection_result['selected_model'] in ['prophet', 'arima']:
            model = selection_result['model_object']
            forecast_df = model.predict(periods=market_data.forecast_periods)
            
            forecast_data = []
            for _, row in forecast_df.iterrows():
                forecast_data.append({
                    "date": row['ds'].isoformat(),
                    "predicted_value": float(row['yhat']),
                    "lower_bound": float(row.get('yhat_lower', row['yhat'] * 0.95)),
                    "upper_bound": float(row.get('yhat_upper', row['yhat'] * 1.05))
                })
            
            return ForecastResponse(
                status="success",
                forecast_data=forecast_data,
                model_used=selection_result['selected_model'],
                accuracy_metrics=selection_result.get('metrics', {}),
                summary={
                    "trend": "upward" if forecast_data[-1]["predicted_value"] > forecast_data[0]["predicted_value"] else "downward",
                    "confidence": "high"
                },
                timestamp=datetime.now().isoformat()
            )
        else:
            raise HTTPException(status_code=500, detail="Model selection failed")
            
    except Exception as e:
        logger.error(f"Forecasting error: {e}")
        raise HTTPException(status_code=500, detail=f"Forecasting failed: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Financial Simulator API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/start-simulation",
            "/simulation/{simulation_id}",
            "/simulations",
            "/forecast"
        ],
        "advanced_forecasting": ADVANCED_FORECASTING
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(
        "langgraph_api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )