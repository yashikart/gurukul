"""
Analytics Routes Module

Provides API endpoints for karmic analytics and visualization.
"""
from fastapi import APIRouter, Query, HTTPException, Response
from typing import Optional
import os
import json
from datetime import datetime
from utils.karmic_analytics import (
    get_weekly_karma_trends,
    get_paap_punya_ratio_trends,
    generate_dharma_seva_flow_chart,
    generate_paap_punya_ratio_chart,
    export_weekly_summary_csv,
    get_live_karmic_metrics
)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/karma_trends")
async def karma_trends(weeks: int = Query(4, ge=1, le=52)):
    """
    Get karmic trends data
    
    Args:
        weeks: Number of weeks to analyze (1-52)
        
    Returns:
        JSON with karmic trends data
    """
    try:
        dharma_seva_trends = get_weekly_karma_trends(weeks)
        paap_punya_trends = get_paap_punya_ratio_trends(weeks)
        
        return {
            "status": "success",
            "data": {
                "dharma_seva_trends": dharma_seva_trends,
                "paap_punya_trends": paap_punya_trends
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating trends: {str(e)}")

@router.get("/charts/dharma_seva_flow")
async def dharma_seva_flow_chart(
    weeks: int = Query(4, ge=1, le=52),
    download: bool = Query(False)
):
    """
    Generate DharmaPoints/SevaPoints flow chart
    
    Args:
        weeks: Number of weeks to analyze (1-52)
        download: Whether to download the chart or display it
        
    Returns:
        Chart image or download link
    """
    try:
        # Generate chart
        filepath = generate_dharma_seva_flow_chart(weeks)
        
        if download:
            # Return download link
            return {
                "status": "success",
                "download_url": f"/analytics_exports/{os.path.basename(filepath)}",
                "filepath": filepath
            }
        else:
            # Return chart info
            return {
                "status": "success",
                "chart_generated": True,
                "filepath": filepath,
                "timestamp": datetime.utcnow().isoformat()
            }
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"Chart generation not available: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@router.get("/charts/paap_punya_ratio")
async def paap_punya_ratio_chart(
    weeks: int = Query(4, ge=1, le=52),
    download: bool = Query(False)
):
    """
    Generate Paap/Punya ratio chart
    
    Args:
        weeks: Number of weeks to analyze (1-52)
        download: Whether to download the chart or display it
        
    Returns:
        Chart image or download link
    """
    try:
        # Generate chart
        filepath = generate_paap_punya_ratio_chart(weeks)
        
        if download:
            # Return download link
            return {
                "status": "success",
                "download_url": f"/analytics_exports/{os.path.basename(filepath)}",
                "filepath": filepath
            }
        else:
            # Return chart info
            return {
                "status": "success",
                "chart_generated": True,
                "filepath": filepath,
                "timestamp": datetime.utcnow().isoformat()
            }
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"Chart generation not available: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@router.get("/exports/weekly_summary")
async def weekly_summary_export(
    weeks: int = Query(4, ge=1, le=52),
    download: bool = Query(True)
):
    """
    Export weekly summary to CSV
    
    Args:
        weeks: Number of weeks to analyze (1-52)
        download: Whether to download the CSV or return file info
        
    Returns:
        CSV file or download link
    """
    try:
        # Export CSV
        filepath = export_weekly_summary_csv(weeks)
        
        if download:
            # Return download link
            return {
                "status": "success",
                "download_url": f"/analytics_exports/{os.path.basename(filepath)}",
                "filepath": filepath
            }
        else:
            # Return file info
            return {
                "status": "success",
                "export_generated": True,
                "filepath": filepath,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting summary: {str(e)}")

@router.get("/metrics/live")
async def live_karmic_metrics():
    """
    Get live karmic metrics
    
    Returns:
        JSON with current karmic metrics
    """
    try:
        metrics = get_live_karmic_metrics()
        return {
            "status": "success",
            "data": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")