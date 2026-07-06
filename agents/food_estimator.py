from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

def create_food_estimator(retry_config: types.HttpRetryOptions) -> Agent:
    return Agent(
        name="FoodEstimator",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""Parse the user's meal description and estimate calories for each item.

Return JSON only with this structure:
{"meal_type": "breakfast|lunch|tea|dinner|snack", "items": [{"name": "food item", "calories": estimated_calories}]}

Be as accurate as possible with your estimates.

Examples:
- "I had coffee and 2 boiled eggs for breakfast" -> {"meal_type": "breakfast", "items": [{"name": "coffee", "calories": 110}, {"name": "boiled egg", "calories": 80}, {"name": "boiled egg", "calories": 80}]}
- "lunch was chicken pulao with salad" -> {"meal_type": "lunch", "items": [{"name": "chicken pulao", "calories": 957}, {"name": "salad", "calories": 50}]}
- "tea time - protein juice and chai" -> {"meal_type": "tea", "items": [{"name": "protein juice", "calories": 135}, {"name": "chai", "calories": 110}]}

Only respond with valid JSON, no other text.""",
        output_key="estimated_meal"
    )

def create_query_classifier(retry_config: types.HttpRetryOptions) -> Agent:
    return Agent(
        name="QueryClassifier",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""Classify what the user is asking about.

Return JSON only with this structure:
{"type": "meal|summary|progress|swap|advice", "content": "the user's query"}

Rules:
- "meal" - User is describing a meal they ate (contains food items)
- "summary" - User is asking for today's summary or total
- "progress" - User is asking about weight progress or goals
- "swap" - User is asking for food alternatives or substitutions
- "advice" - User is asking for general advice or recommendations

Examples:
- "I had coffee and 2 boiled eggs for breakfast" -> {"type": "meal", "content": "I had coffee and 2 boiled eggs for breakfast"}
- "How's my daily total?" -> {"type": "summary", "content": "How's my daily total?"}
- "What's my weight progress?" -> {"type": "progress", "content": "What's my weight progress?"}
- "Can you suggest a swap for bhel puri?" -> {"type": "swap", "content": "Can you suggest a swap for bhel puri?"}

Only respond with valid JSON, no other text.""",
        output_key="query_type"
    )