import json
import os

USER_PROFILE = {}

def load_user_profile():
    """Load user profile from JSON file"""
    global USER_PROFILE
    profile_path = "data/user_profile.json"
    
    try:
        with open(profile_path, 'r') as f:
            USER_PROFILE = json.load(f)
            return USER_PROFILE
    except FileNotFoundError:
        default_profile = {
            "weight": 77.55,
            "height": 180,
            "age": 32,
            "gender": "male",
            "activity_level": 1.3,
            "target_weight": 70,
            "initial_weight": 91.2
        }
        os.makedirs("data", exist_ok=True)
        with open(profile_path, 'w') as f:
            json.dump(default_profile, f, indent=2)
        USER_PROFILE = default_profile
        return default_profile
    except Exception as e:
        print(f"Error loading profile: {e}")
        return None

def calculate_tdee(weight: float = None, height: float = None, 
                   age: int = None, activity: float = None) -> dict:
    """Calculate TDEE using Harris-Benedict equation"""
    global USER_PROFILE
    
    if not USER_PROFILE:
        load_user_profile()
    
    w = weight or USER_PROFILE.get("weight", 77.55)
    h = height or USER_PROFILE.get("height", 180)
    a = age or USER_PROFILE.get("age", 32)
    act = activity or USER_PROFILE.get("activity_level", 1.3)
    
    bmr = (10 * w) + (6.25 * h) - (5 * a) + 5
    tdee = bmr * act
    
    return {
        "bmr": round(bmr, 2),
        "tdee": round(tdee, 2),
        "activity_level": act,
        "weight": w
    }

# Load profile on import
load_user_profile()