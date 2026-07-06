from datetime import datetime
import json
import os

DAILY_LOG = {}

def load_data(filepath: str = "data/daily_log.json") -> bool:
    """Load daily log from file"""
    global DAILY_LOG
    try:
        with open(filepath, 'r') as f:
            DAILY_LOG = json.load(f)
        return True
    except FileNotFoundError:
        DAILY_LOG = {}
        return False
    except Exception:
        return False

def save_data(filepath: str = "data/daily_log.json") -> bool:
    """Save daily log to file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(DAILY_LOG, f, indent=2)
        return True
    except Exception:
        return False

def track_meal(date: str, meal_type: str, items: list) -> dict:
    """Store meal in daily log"""
    if date not in DAILY_LOG:
        DAILY_LOG[date] = {"meals": [], "total": 0}
    
    meal_total = sum(item.get("calories", 0) for item in items)
    DAILY_LOG[date]["meals"].append({
        "type": meal_type,
        "items": items,
        "total": meal_total,
        "timestamp": datetime.now().isoformat()
    })
    DAILY_LOG[date]["total"] += meal_total
    
    from .calorie_tools import calculate_tdee
    tdee_data = calculate_tdee()
    
    return {
        "status": "success",
        "meal_type": meal_type,
        "meal_calories": meal_total,
        "daily_total": DAILY_LOG[date]["total"],
        "tdee": tdee_data["tdee"],
        "remaining": tdee_data["tdee"] - DAILY_LOG[date]["total"],
        "on_track": DAILY_LOG[date]["total"] <= tdee_data["tdee"],
        "items": items,
        "date": date
    }

# Load data on import
load_data()