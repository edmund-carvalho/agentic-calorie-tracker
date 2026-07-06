from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types

def create_advisor(retry_config: types.HttpRetryOptions) -> Agent:
    from tools.analytics_tools import (
        get_daily_summary, get_weekly_summary,
        get_weight_progress, suggest_swap
    )
    from tools.calorie_tools import calculate_tdee
    from tools.tracking_tools import get_todays_log
    
    return Agent(
        name="Advisor",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""You are a nutrition advisor. Analyze the user's data and provide helpful advice.
Consider patterns, progress, and practical suggestions.
Use the available tools to access data.
Be supportive and practical.""",
        tools=[
            FunctionTool(get_daily_summary),
            FunctionTool(get_weekly_summary),
            FunctionTool(get_weight_progress),
            FunctionTool(suggest_swap),
            FunctionTool(calculate_tdee),
            FunctionTool(get_todays_log)
        ],
        output_key="advice"
    )