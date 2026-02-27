from fastapi import APIRouter, HTTPException
from firebase_client import get_db
from config import get_sport_category
from services.strava_service import (
    refresh_access_token,
    get_recent_activities,
    get_activity_detail,
    get_athlete_profile,
)
from datetime import datetime

router = APIRouter(prefix="/api/sync", tags=["sync"])

@router.get("/test/{player_id}")
async def test_sync_logic(player_id: str):
    """
    Fetch last 5 activities, map them, and return as JSON without storing.
    Used for testing Strava connection and calorie fallback chain.
    """
    db = get_db()
    
    # 1. Fetch player and token
    player_doc = db.collection("athletes").document(player_id).get()
    if not player_doc.exists:
        raise HTTPException(status_code=404, detail="Player not found")
    
    access_token = await refresh_access_token(player_id)
    
    # 2. Get weight for MET estimation fallback
    athlete_profile = await get_athlete_profile(access_token)
    weight_kg = athlete_profile.get("weight", 80) or 80
    
    MET_VALUES = {
        "Running": 9.8,
        "Cycling": 7.5,
        "Swimming": 8.0,
    }
    
    # 3. Get recent activities
    activities = await get_recent_activities(access_token, count=5)
    test_results = []
    
    for activity in activities:
        # Fetch details for calories
        detail = await get_activity_detail(access_token, activity["id"])
        
        # Mapping logic (replicated from sync_service)
        sport_type = activity.get("sport_type", "")
        sport_category = get_sport_category(sport_type)
        
        calories = detail.get("calories", 0) or 0
        kilojoules = detail.get("kilojoules", 0) or 0
        moving_time_seconds = activity.get("moving_time", 0) or 0
        
        calorie_source = "strava_native"
        if calories == 0:
            if kilojoules > 0:
                calories = round(kilojoules * 0.239, 2)
                calorie_source = "kilojoules_derived"
            else:
                met = MET_VALUES.get(sport_category, 1.0)
                duration_hours = moving_time_seconds / 3600.0
                calories = round(met * weight_kg * duration_hours, 2)
                calorie_source = "met_estimated"
                
        test_results.append({
            "name": activity.get("name"),
            "sport_type": sport_type,
            "sport_category": sport_category,
            "start_date": activity.get("start_date"),
            "distance_meters": activity.get("distance"),
            "moving_time_seconds": moving_time_seconds,
            "strava_calories": detail.get("calories"),
            "strava_kilojoules": detail.get("kilojoules"),
            "calculated_calories": calories,
            "calorie_source": calorie_source,
            "weight_used": weight_kg
        })
        
    return {
        "player_id": player_id,
        "athlete_weight": weight_kg,
        "recent_activities": test_results
    }
