from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types

def create_tracker(retry_config: types.HttpRetryOptions) -> Agent:
    from tools.tracking_tools import track_meal, save_data
    from tools.calorie_tools import calculate_tdee
    
    return Agent(
        name="Tracker",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""Track the meal using track_meal tool. Show:
1. What was logged with calories
2. Total for this meal
3. Running daily total
4. Remaining calories
5. Whether they're on track

Be clear and encouraging.""",
        tools=[
            FunctionTool(track_meal),
            FunctionTool(calculate_tdee),
            FunctionTool(save_data)
        ],
        output_key="tracking_result"
    )