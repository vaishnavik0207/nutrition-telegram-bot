import json
import requests
import os
from datetime import datetime, timedelta
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

NUTRITIONIX_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
NUTRITIONIX_API_KEY = os.getenv("NUTRITIONIX_API_KEY") 
MEAL_FILE = os.getenv("MEAL_DATA_PATH", "meal_data.json")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@tool("detect_meal_type")
def detect_meal_type(user_input: str) -> str:
    """Check if user mentioned breakfast, lunch, dinner, or snack. Return 'unknown' if not found."""
    text = user_input.lower()
    
    if any(word in text for word in ["breakfast", "morning"]):
        return "breakfast"
    elif any(word in text for word in ["lunch", "noon", "afternoon"]):
        return "lunch"  
    elif any(word in text for word in ["dinner", "evening", "night", "supper"]):
        return "dinner"
    elif any(word in text for word in ["snack", "snacking"]):
        return "snack"
    
    return "unknown"

@tool("get_nutrition_data")
def get_nutrition_data(food_input: str) -> str:
    """Get nutrition info from Nutritionix API"""
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            "https://trackapi.nutritionix.com/v2/natural/nutrients",
            headers=headers,
            json={"query": food_input}
        )
        response.raise_for_status()
        return response.text
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool("format_nutrition_facts")
def format_nutrition_facts(nutrition_json: str) -> str:
    """Show detailed nutrition breakdown with calories, protein, carbs, fat, fiber"""
    try:
        data = json.loads(nutrition_json)
        
        if "foods" not in data or not data["foods"]:
            return "No nutrition data found."
        
        foods = data["foods"]
        
        # Calculate totals
        total_calories = sum(food.get("nf_calories", 0) for food in foods)
        total_protein = sum(food.get("nf_protein", 0) for food in foods)
        total_carbs = sum(food.get("nf_total_carbohydrate", 0) for food in foods)
        total_fat = sum(food.get("nf_total_fat", 0) for food in foods)
        total_fiber = sum(food.get("nf_dietary_fiber", 0) for food in foods)
        total_sugar = sum(food.get("nf_sugars", 0) for food in foods)
        
        # Build response
        response = []
        response.append("📊 **NUTRITION BREAKDOWN**")
        response.append(f"🔥 Calories: {total_calories:.0f} kcal")
        response.append(f"💪 Protein: {total_protein:.1f}g")
        response.append(f"🍞 Carbs: {total_carbs:.1f}g")
        response.append(f"🥑 Fat: {total_fat:.1f}g") 
        response.append(f"🌾 Fiber: {total_fiber:.1f}g")
        response.append(f"🍭 Sugar: {total_sugar:.1f}g")
        response.append("")
        
        # Show individual items
        response.append("**Food Items:**")
        for i, food in enumerate(foods, 1):
            name = food.get("food_name", "Unknown")
            cals = food.get("nf_calories", 0)
            response.append(f"{i}. {name} - {cals:.0f} kcal")
        
        return "\n".join(response)
        
    except Exception as e:
        return f"Error formatting: {str(e)}"

@tool("save_meal_data")
def save_meal_data(meal_info: str) -> str:
    """Save meal info to JSON file"""
    try:
        data = json.loads(meal_info)
        
        meals = {}
        if os.path.exists(MEAL_FILE):
            with open(MEAL_FILE, "r") as f:
                meals = json.load(f)
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in meals:
            meals[today] = []
        meals[today].append(data)
        
        with open(MEAL_FILE, "w") as f:
            json.dump(meals, f, indent=2)
        
        return "✅ Meal saved successfully!"
        
    except Exception as e:
        return f"❌ Save failed: {str(e)}"

@tool("generate_health_advice")
def generate_health_advice(nutrition_json: str) -> str:
    """Give health tips based on nutrition data"""
    try:
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            openai_api_key=OPENAI_API_KEY,
            temperature=0.3
        )
        
        prompt = f"""Based on this nutrition data, give 2-3 practical health tips:
{nutrition_json}

Keep it friendly, specific, and under 100 words!"""
        
        response = llm.invoke(prompt)
        return "💡 **Health Tips:**\n" + response.content
        
    except Exception as e:
        return f"Advice failed: {str(e)}"

@tool("get_meal_history")
def get_meal_history(timeframe: str) -> str:
    """Show meal history for today or specific date"""
    try:
        if not os.path.exists(MEAL_FILE):
            return "No meal history yet!"
        
        with open(MEAL_FILE, "r") as f:
            meals = json.load(f)
        
        if timeframe == "today":
            date = datetime.now().strftime("%Y-%m-%d")
        elif timeframe == "yesterday":
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            date = timeframe
        
        if date not in meals:
            return f"No meals for {date}"
        
        history = [f"📅 Meals for {date}:"]
        for meal in meals[date]:
            meal_type = meal.get("meal_type", "meal").title()
            history.append(f"\n{meal_type}:")
            
            foods = meal.get("nutrition_data", {}).get("foods", [])
            for food in foods:
                name = food.get("food_name", "Unknown")
                cals = food.get("nf_calories", 0)
                history.append(f"  • {name} - {cals:.0f} cal")
        
        return "\n".join(history)
        
    except Exception as e:
        return f"History error: {str(e)}"

# All tools together
tools = [detect_meal_type, get_nutrition_data, format_nutrition_facts, save_meal_data, generate_health_advice, get_meal_history]