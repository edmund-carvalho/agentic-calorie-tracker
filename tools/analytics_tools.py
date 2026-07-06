from .tracking_tools import DAILY_LOG
from .calorie_tools import calculate_tdee, USER_PROFILE
from datetime import datetime

def get_daily_summary(date: str) -> dict:
    """Get summary for a specific date"""
    if date not in DAILY_LOG:
        return {"status": "error", "message": "No meals logged for this date"}
    
    tdee_data = calculate_tdee()
    day = DAILY_LOG[date]
    
    return {
        "status": "success",
        "date": date,
        "total": day["total"],
        "tdee": tdee_data["tdee"],
        "remaining": tdee_data["tdee"] - day["total"],
        "on_track": day["total"] <= tdee_data["tdee"],
        "meals": day["meals"],
        "meal_count": len(day["meals"])
    }

def get_weekly_summary() -> dict:
    """Get summary for the last 7 days"""
    dates = sorted(DAILY_LOG.keys(), reverse=True)[:7]
    if not dates:
        return {"status": "error", "message": "No data available"}
    
    week_data = []
    tdee_data = calculate_tdee()
    
    for date in dates:
        day = DAILY_LOG[date]
        week_data.append({
            "date": date,
            "total": day["total"],
            "tdee": tdee_data["tdee"],
            "remaining": tdee_data["tdee"] - day["total"],
            "on_track": day["total"] <= tdee_data["tdee"]
        })
    
    avg_calories = sum(d["total"] for d in week_data) / len(week_data)
    avg_deficit = tdee_data["tdee"] - avg_calories
    
    return {
        "status": "success",
        "days_tracked": len(week_data),
        "average_calories": round(avg_calories, 2),
        "average_deficit": round(avg_deficit, 2),
        "projected_loss": round((avg_deficit * 7) / 7700, 3),
        "days": week_data
    }

def get_weight_progress() -> dict:
    """Track progress toward weight goal"""
    current = USER_PROFILE.get("weight", 77.55)
    initial = USER_PROFILE.get("initial_weight", 91.2)
    target = USER_PROFILE.get("target_weight", 70)
    
    lost = initial - current
    remaining = current - target
    progress_pct = (lost / (initial - target)) * 100 if (initial - target) > 0 else 0
    
    weekly = get_weekly_summary()
    weeks_to_goal = None
    if weekly["status"] == "success" and weekly["projected_loss"] > 0:
        weeks_to_goal = remaining / weekly["projected_loss"]
    
    return {
        "status": "success",
        "current_weight": current,
        "initial_weight": initial,
        "target_weight": target,
        "total_lost": round(lost, 2),
        "remaining_to_goal": round(remaining, 2),
        "progress_percentage": round(progress_pct, 2),
        "weeks_to_goal": round(weeks_to_goal, 1) if weeks_to_goal else None
    }

def suggest_swap(food_name: str) -> dict:
    """Suggest a lower-calorie alternative"""
    swaps = {
        "bhel puri": {"suggested": "carrot sandwich", "saves": 130},
        "masala dosa": {"suggested": "thali", "saves": 100},
        "idly vada": {"suggested": "thali", "saves": 160},
        "puri bhaji": {"suggested": "thali", "saves": 100},
        "chicken wings": {"suggested": "egg sandwich", "saves": 130},
        "potato wedges": {"suggested": "protein shake", "saves": 70}
    }
    
    food = food_name.lower().strip()
    if food in swaps:
        return {
            "status": "success",
            "current": food,
            "suggested": swaps[food]["suggested"],
            "saves": swaps[food]["saves"],
            "message": f"Swap {food} for {swaps[food]['suggested']} - Save {swaps[food]['saves']} kcal"
        }
    
    matches = [f for f in swaps.keys() if f in food or food in f]
    if matches:
        return {
            "status": "partial",
            "message": f"No exact swap found for '{food_name}'. Did you mean: {', '.join(matches[:3])}?",
            "suggestions": matches[:3]
        }
    
    return {
        "status": "error",
        "message": f"No swap suggestions available for '{food_name}'"
    }