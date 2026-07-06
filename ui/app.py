"""Streamlit UI for Calorie Tracker"""

import streamlit as st
import json
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.calorie_tools import USER_PROFILE, calculate_tdee, load_user_profile
from tools.tracking_tools import DAILY_LOG, track_meal, save_data, get_todays_log, clear_todays_log
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
                    
                    today_log = get_todays_log()
                    if today_log["meals"]:
                        last_meal = today_log["meals"][-1]
                        st.success(f"✅ {meal_type.title()} logged! ({last_meal['total']} kcal)")
                        
                        st.write("**Items logged:**")
                        for item in last_meal["items"]:
                            st.write(f"  • {item['name']}: {item['calories']} kcal")
                        
                        tdee = calculate_tdee()["tdee"]
                        remaining = tdee - today_log["total"]
                        st.metric("Daily Total", f"{today_log['total']} kcal")
                        st.metric("Remaining", f"{remaining} kcal")
                        st.metric("Status", "✅ On Track" if remaining >= 0 else "⚠️ Over Budget")
                    else:
                        st.warning("No meals were logged. Please check the meal description.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

with col2:
    st.header("📊 Today's Summary")
    today_log = get_todays_log()
    tdee_data = calculate_tdee()
    
    if today_log["meals"]:
        total = today_log["total"]
        remaining = tdee_data["tdee"] - total
        
        st.metric("Total", f"{total} kcal")
        st.metric("Remaining", f"{remaining} kcal")
        st.metric("Status", "✅ On Track" if remaining >= 0 else "⚠️ Over Budget")
        
        for meal in today_log["meals"]:
            with st.expander(f"🍽️ {meal['type'].title()} ({meal['total']} kcal)"):
                for item in meal["items"]:
                    st.write(f"• {item['name']}: {item['calories']} kcal")
                st.caption(f"Logged at: {meal['timestamp']}")
    else:
        st.info("No meals logged today")
        
        quick_meals = [
            ("Coffee", 110),
            ("Boiled Egg", 80),
            ("Apple", 95),
            ("Banana", 80)
        ]
        cols = st.columns(2)
        for i, (name, calories) in enumerate(quick_meals):
            if cols[i % 2].button(f"➕ {name}"):
                items = [{"name": name, "calories": calories}]
                result = track_meal("snack", items)
                save_data()
                st.success(f"Logged {name} ({calories} kcal)")
                st.rerun()
    
    if st.button("🗑️ Clear Today's Log", type="secondary"):
        clear_todays_log()
        save_data()
        st.success("Today's log cleared!")
        st.rerun()

# ==================== NEW: View Past Meals ====================

st.header("📅 View Past Meals")

# Get all dates that have data
all_dates = sorted(DAILY_LOG.keys(), reverse=True)

if all_dates:
    # Date selector
    selected_date = st.selectbox(
        "Select a date to view",
        options=all_dates,
        format_func=lambda x: f"{x} ({len(DAILY_LOG[x]['meals'])} meals, {DAILY_LOG[x]['total']} kcal)"
    )
    
    if selected_date:
        day_data = DAILY_LOG[selected_date]
        tdee_data = calculate_tdee()
        remaining = tdee_data["tdee"] - day_data["total"]
        
        col_prev, col_prev2, col_prev3 = st.columns(3)
        with col_prev:
            st.metric("Total", f"{day_data['total']} kcal")
        with col_prev2:
            st.metric("Remaining", f"{remaining} kcal")
        with col_prev3:
            st.metric("Status", "✅ On Track" if remaining >= 0 else "⚠️ Over Budget")
        
        for meal in day_data["meals"]:
            with st.expander(f"🍽️ {meal['type'].title()} ({meal['total']} kcal)"):
                for item in meal["items"]:
                    st.write(f"• {item['name']}: {item['calories']} kcal")
                st.caption(f"Logged at: {meal['timestamp']}")
else:
    st.info("No past meals found. Start logging to see your history!")

# Smart Swap Section
st.header("💡 Smart Swap Suggestions")
col3, col4 = st.columns(2)

with col3:
    craving = st.text_input("What are you craving?", placeholder="e.g., bhel puri")
    if st.button("🔍 Suggest Swap"):
        if craving:
            result = suggest_swap(craving)
            if result["status"] == "success":
                st.success(result["message"])
                st.metric("Calories Saved", f"{result['saves']} kcal")
                st.info(f"💡 {result['message']}")
            elif result["status"] == "partial":
                st.warning(result["message"])
                if "suggestions" in result:
                    st.write("**Did you mean one of these?**")
                    for s in result["suggestions"]:
                        st.write(f"  • {s}")
            else:
                st.warning(result["message"])
        else:
            st.info("Enter a food to find alternatives")

with col4:
    if st.button("📊 Show Weekly Summary"):
        weekly = get_weekly_summary()
        if weekly["status"] == "success":
            st.subheader("📊 Weekly Stats")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Avg Daily", f"{weekly['average_calories']} kcal")
            with col_b:
                st.metric("Avg Deficit", f"{weekly['average_deficit']} kcal")
            with col_c:
                st.metric("Projected Loss", f"{weekly['projected_loss']} kg")
            
            st.write("**Daily Breakdown:**")
            for day in weekly["days"]:
                status = "✅" if day['on_track'] else "⚠️"
                st.write(f"{day['date']}: {day['total']} kcal {status}")
        else:
            st.warning(weekly["message"])

# Weight Progress Section
st.header("📈 Weight Progress")
progress = get_weight_progress()
if progress["status"] == "success":
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Current", f"{progress['current_weight']} kg")
    with col6:
        st.metric("Lost", f"{progress['total_lost']} kg")
    with col7:
        st.metric("Remaining", f"{progress['remaining_to_goal']} kg")
    with col8:
        st.metric("Progress", f"{progress['progress_percentage']}%")
    
    if progress['weeks_to_goal']:
        st.info(f"📅 Estimated time to reach goal: {progress['weeks_to_goal']} weeks at current rate")

# Footer
st.divider()
st.caption("⚠️ Disclaimer: This is a proof-of-concept for educational purposes. Not a health or medical device. Always consult qualified professionals for health decisions.")