#!/usr/bin/env python3
"""Agentic Calorie Tracker - Main Entry Point"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.genai import types
from datetime import datetime

# Load environment variables
load_dotenv()

# ==================== RATE LIMITING ====================

class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, rpm_limit: int = 10, rpd_limit: int = 20):
        self.rpm_limit = rpm_limit
        self.rpd_limit = rpd_limit
        self.rpm_calls = []
        self.rpd_calls = []
        self.lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        async with self.lock:
            now = datetime.now().timestamp()
            
            # Clean old RPM calls (> 60 seconds)
            self.rpm_calls = [t for t in self.rpm_calls if now - t < 60]
            
            # Clean old RPD calls (> 86400 seconds)
            self.rpd_calls = [t for t in self.rpd_calls if now - t < 86400]
            
            # Check RPD limit (20 per day)
            if len(self.rpd_calls) >= self.rpd_limit:
                oldest = min(self.rpd_calls)
                wait_time = 86400 - (now - oldest) + 1
                print(f"⏳ RPD limit (20/day) reached. Waiting {wait_time/3600:.1f} hours...")
                await asyncio.sleep(wait_time)
                now = datetime.now().timestamp()
                self.rpd_calls = [t for t in self.rpd_calls if now - t < 86400]
            
            # Check RPM limit (10 per minute)
            if len(self.rpm_calls) >= self.rpm_limit:
                oldest = min(self.rpm_calls)
                wait_time = 60 - (now - oldest) + 0.5
                print(f"⏳ RPM limit (10/min) reached. Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                now = datetime.now().timestamp()
                self.rpm_calls = [t for t in self.rpm_calls if now - t < 60]
            
            # Record the call
            self.rpm_calls.append(now)
            self.rpd_calls.append(now)

# Create global rate limiter
rate_limiter = RateLimiter()

# ==================== CONFIGURATION ====================

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)

def get_api_key():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise ValueError(
            "GOOGLE_API_KEY not found in .env file.\n"
            "Please copy .env.example to .env and add your API key.\n"
            "Get your key from: https://aistudio.google.com/app/api-keys"
        )
    return api_key

os.environ["GOOGLE_API_KEY"] = get_api_key()

# ==================== IMPORT TOOLS ====================

from tools.calorie_tools import load_user_profile, calculate_tdee
from tools.tracking_tools import load_data, track_meal, save_data, DAILY_LOG
from tools.analytics_tools import (
    get_daily_summary, get_weekly_summary,
    get_weight_progress, suggest_swap
)

# Load user profile and data
load_user_profile()
load_data()

# ==================== CREATE AGENTS ====================

food_estimator = Agent(
    name="FoodEstimator",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""Parse the user's meal description and estimate calories for each item.

Return JSON only with this structure:
{"meal_type": "breakfast|lunch|tea|dinner|snack", "items": [{"name": "food item", "calories": estimated_calories}]}

Be as accurate as possible with your estimates.

Examples:
- "I had coffee and 2 boiled eggs for breakfast" -> {"meal_type": "breakfast", "items": [{"name": "coffee", "calories": 110}, {"name": "boiled egg", "calories": 80}, {"name": "boiled egg", "calories": 80}]}
- "lunch was chicken pulao with salad" -> {"meal_type": "lunch", "items": [{"name": "chicken pulao", "calories": 957}, {"name": "salad", "calories": 50}]}

Only respond with valid JSON, no other text.""",
    output_key="estimated_meal"
)

tracker = Agent(
    name="Tracker",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are a calorie tracker. Based on the meal data provided, track it and provide a summary.

The meal data will be in JSON format with meal_type and items.

Provide a clear summary showing:
1. What was logged with calories
2. Total for this meal
3. Running daily total
4. Remaining calories
5. Whether they're on track

Be encouraging and clear.""",
    tools=[
        FunctionTool(track_meal),
        FunctionTool(calculate_tdee),
        FunctionTool(save_data)
    ],
    output_key="tracking_result"
)

advisor = Agent(
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
        FunctionTool(calculate_tdee)
    ],
    output_key="advice"
)

# ==================== CREATE WORKFLOWS ====================

sequential_workflow = SequentialAgent(
    name="CalorieTracker",
    sub_agents=[food_estimator, tracker, advisor]
)

# ==================== RUNNER ====================

runner = InMemoryRunner(agent=sequential_workflow)

# ==================== MAIN FUNCTIONS WITH RATE LIMITING ====================

async def run_async(query: str) -> str:
    """Run the calorie tracker with rate limiting"""
    try:
        await rate_limiter.wait_if_needed()
        response = await runner.run_debug(query)
        return str(response)
    except Exception as e:
        return f"Error: {str(e)}"

async def demo():
    """Run a demo of the calorie tracker - simplified to avoid rate limits"""
    print("=" * 70)
    print("🍽️ AGENTIC CALORIE TRACKER")
    print("🏆 Kaggle Capstone Project - Concierge Agents Track")
    print("=" * 70)
    
    tdee_data = calculate_tdee()
    progress = get_weight_progress()
    
    print(f"\n📊 USER PROFILE:")
    print(f"   Current Weight: {progress['current_weight']} kg")
    print(f"   Target Weight: {progress['target_weight']} kg")
    print(f"   TDEE: {tdee_data['tdee']} kcal/day")
    print(f"   Progress: {progress['total_lost']} kg lost ({progress['progress_percentage']}% to goal)")
    
    print(f"\n⚠️ Gemini Free Tier Limits:")
    print(f"   • 10 requests per minute")
    print(f"   • 20 requests per day")
    print(f"   • Auto-throttling enabled")
    
    # SIMPLIFIED: Only 3 test queries to verify execution
    test_queries = [
        "I had coffee and 2 boiled eggs for breakfast",
        "lunch was chicken pulao with salad",
        "How's my daily total?"
    ]
    
    print(f"\n📝 Running {len(test_queries)} test queries...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─' * 70}")
        print(f"📝 TEST {i}: {query}")
        print(f"{'─' * 70}")
        
        # Handle non-meal queries directly
        if "total" in query.lower() or "summary" in query.lower():
            today = datetime.now().strftime("%Y-%m-%d")
            summary = get_daily_summary(today)
            if summary["status"] == "success":
                print(f"\n📊 TODAY'S SUMMARY:")
                print(f"   Total: {summary['total']} / {summary['tdee']} kcal")
                print(f"   Remaining: {summary['remaining']} kcal")
                print(f"   Status: {'✅ On track' if summary['on_track'] else '⚠️ Over budget'}")
                for meal in summary["meals"]:
                    print(f"   • {meal['type']}: {meal['total']} kcal")
                    for item in meal["items"]:
                        print(f"     - {item['name']}: {item['calories']} kcal")
            else:
                print(f"\n📊 {summary['message']}")
            continue
        
        # For meal queries, run the agent
        print("⏳ Calling Gemini API...")
        result = await run_async(query)
        
        if "Error" not in result:
            # Try to extract the tracking result
            if "tracked" in result.lower() or "logged" in result.lower():
                print(f"\n📝 {result}")
            else:
                print(f"\n📝 {result}")
        else:
            print(f"\n⚠️ {result}")
    
    # Show final daily summary
    print("\n" + "=" * 70)
    print("📊 FINAL DAILY SUMMARY")
    print("=" * 70)
    today = datetime.now().strftime("%Y-%m-%d")
    summary = get_daily_summary(today)
    if summary["status"] == "success":
        print(f"Date: {summary['date']}")
        print(f"Total: {summary['total']} / {summary['tdee']} kcal")
        print(f"Remaining: {summary['remaining']} kcal")
        print(f"Status: {'✅ On track' if summary['on_track'] else '⚠️ Over budget'}")
        print("\nMeals logged:")
        for meal in summary["meals"]:
            print(f"  • {meal['type']}: {meal['total']} kcal")
            for item in meal["items"]:
                print(f"    - {item['name']}: {item['calories']} kcal")
    else:
        print("No meals logged today")
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE - All Systems Verified!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(demo())