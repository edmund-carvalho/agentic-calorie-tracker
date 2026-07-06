from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types
import json

def create_tracker(retry_config: types.HttpRetryOptions) -> Agent:
    from tools.tracking_tools import track_meal, save_data, track_multiple_meals
    from tools.calorie_tools import calculate_tdee
    
    return Agent(
        name="Tracker",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""You are a calorie tracker. Based on the meal data provided, track it and provide a summary.

The meal data will be a JSON array with one or more meals:
[{"meal_type": "breakfast", "items": [...]}, {"meal_type": "lunch", "items": [...]}]

Call track_multiple_meals() with the entire meal array - it will handle all meals at once.

Provide a clear summary showing:
1. What was logged with calories for each meal
2. Total for all meals
3. Running daily total
4. Remaining calories
5. Whether they're on track

Be encouraging and clear.""",
        tools=[
            FunctionTool(track_multiple_meals),
            FunctionTool(track_meal),
            FunctionTool(calculate_tdee),
            FunctionTool(save_data)
        ],
        output_key="tracking_result"
    )