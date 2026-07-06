"""Streamlit UI for Calorie Tracker"""

import streamlit as st
import json
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.calorie_tools import USER_PROFILE, calculate_tdee, load_user_profile
from tools.tracking_tools import DAILY_LOG, track_meal, save_data
from tools.analytics_tools import get_daily_summary, get_weight_progress, suggest_swap, get_weekly_summary

st.set_page_config(
    page_title="🍽️ Calorie Tracker",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ Agentic Calorie Tracker")
st.subheader("Your Personal AI Nutritionist")

# Sidebar
with st.sidebar:
    st.header("📊 User Profile")
    
    # Load current profile
    profile = load_user_profile()
    
    weight = st.number_input("Weight (kg)", value=float(profile["weight"]), step=0.1)
    height = st.number_input("Height (cm)", value=int(profile["height"]))
    age = st.number_input("Age", value=int(profile["age"]))
    target = st.number_input("Target Weight (kg)", value=float(profile["target_weight"]), step=0.1)
    initial = st.number_input("Initial Weight (kg)", value=float(profile["initial_weight"]), step=0.1)
    
    activity_levels = {
        1.2: "Sedentary",
        1.375: "Lightly Active",
        1.55: "Moderately Active",
        1.725: "Very Active",
        1.9: "Extremely Active"
    }
    current_activity = profile.get("activity_level", 1.3)
    activity_label = activity_levels.get(current_activity, "Lightly Active")
    activity = st.selectbox(
        "Activity Level",
        options=list(activity_levels.keys()),
        format_func=lambda x: activity_levels[x],
        index=list(activity_levels.keys()).index(current_activity) if current_activity in activity_levels else 1
    )
    
    if st.button("💾 Save Profile"):
        updated_profile = {
            "weight": weight,
            "height": height,
            "age": age,
            "gender": profile.get("gender", "male"),
            "activity_level": activity,
            "target_weight": target,
            "initial_weight": initial
        }
        
        with open("data/user_profile.json", 'w') as f:
            json.dump(updated_profile, f, indent=2)
        
        st.success("✅ Profile saved!")
        st.rerun()
    
    tdee_data = calculate_tdee()
    st.metric("TDEE", f"{tdee_data['tdee']} kcal/day")
    
    progress = get_weight_progress()
    if progress["status"] == "success":
        st.metric("Progress", f"{progress['progress_percentage']}%")
        st.metric("Lost", f"{progress['total_lost']} kg")
        st.metric("Remaining", f"{progress['remaining_to_goal']} kg")

# Main area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 Log Your Meal")
    
    meal_type = st.selectbox("Meal Type", ["breakfast", "lunch", "tea", "dinner", "snack"])
    meal_description = st.text_area("What did you eat?", placeholder="e.g., coffee and 2 boiled eggs")
    
    if st.button("Log Meal", type="primary"):
        if meal_description:
            try:
                from agent import run_sync
                with st.spinner("Processing..."):
                    result = run_sync(f"I had {meal_description} for {meal_type}")
                    st.success("✅ Meal logged!")
                    st.write(result)
            except Exception as e:
                st.error(f"Error: {str(e)}")

with col2:
    st.header("📊 Today's Summary")
    today = datetime.now().strftime("%Y-%m-%d")
    summary = get_daily_summary(today)
    
    if summary["status"] == "success":
        st.metric("Total", f"{summary['total']} kcal")
        st.metric("Remaining", f"{summary['remaining']} kcal")
        st.metric("Status", "✅ On Track" if summary["on_track"] else "⚠️ Over Budget")
        
        for meal in summary["meals"]:
            with st.expander(f"🍽️ {meal['type'].title()} ({meal['total']} kcal)"):
                for item in meal["items"]:
                    st.write(f"• {item['name']}: {item['calories']} kcal")
    else:
        st.info("No meals logged today")

# Smart Swap Section
st.header("💡 Smart Swap Suggestions")
col3, col4 = st.columns(2)

with col3:
    craving = st.text_input("What are you craving?", placeholder="e.g., bhel puri")
    if st.button("Suggest Swap"):
        result = suggest_swap(craving)
        if result["status"] == "success":
            st.success(result["message"])
            st.metric("Calories Saved", f"{result['saves']} kcal")
        else:
            st.warning(result["message"])

with col4:
    if st.button("Show Weekly Summary"):
        weekly = get_weekly_summary()
        if weekly["status"] == "success":
            st.subheader("📊 Weekly Stats")
            st.metric("Avg Daily", f"{weekly['average_calories']} kcal")
            st.metric("Projected Loss", f"{weekly['projected_loss']} kg/week")
            for day in weekly["days"]:
                st.write(f"{day['date']}: {day['total']} kcal {'✅' if day['on_track'] else '⚠️'}")