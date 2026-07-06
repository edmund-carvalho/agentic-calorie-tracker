from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

def create_food_estimator(retry_config: types.HttpRetryOptions) -> Agent:
    return Agent(
        name="FoodEstimator",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""Parse the user's meal description and estimate calories for each item.

Return a SINGLE JSON array with all meals. Do NOT return multiple separate JSON objects.

Format:
[
    {"meal_type": "breakfast|lunch|tea|dinner|snack", "items": [{"name": "food item", "calories": estimated_calories}]},
    {"meal_type": "lunch", "items": [{"name": "food item", "calories": estimated_calories}]}
]

Examples:
- "I had coffee and 2 boiled eggs for breakfast" -> 
[{"meal_type": "breakfast", "items": [{"name": "coffee", "calories": 110}, {"name": "boiled egg", "calories": 80}, {"name": "boiled egg", "calories": 80}]}]

- "breakfast: coffee, lunch: chicken pulao" -> 
[{"meal_type": "breakfast", "items": [{"name": "coffee", "calories": 110}]}, {"meal_type": "lunch", "items": [{"name": "chicken pulao", "calories": 957}]}]

Only respond with valid JSON array, no other text.""",
        output_key="estimated_meal"
    )

def create_query_classifier(retry_config: types.HttpRetryOptions) -> Agent:
    return Agent(
        name="QueryClassifier",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""Classify what the user is asking about.
Return JSON: {"type": "meal|summary|progress|swap|advice", "content": "the user's query"}""",
        output_key="query_type"
    )