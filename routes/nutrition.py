"""
FitVerse — Nutrition Routes
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import date, timedelta
from models import db, MealLog
from watsonx_client import get_watsonx_client

nutrition_bp = Blueprint("nutrition", __name__)

DIET_TYPES = ["Vegetarian", "Vegan", "Non-Vegetarian", "High-Protein", "Keto", "Mediterranean"]
MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snack"]

INDIAN_MEALS = {
    "breakfast": ["Poha with peanuts", "Idli with sambar", "Upma", "Paratha with curd", "Oats with fruits", "Moong dal cheela"],
    "lunch": ["Dal rice with sabzi", "Rajma chawal", "Chole with roti", "Mixed veg with phulka", "Palak paneer with rice"],
    "dinner": ["Khichdi with papad", "Dal tadka with roti", "Stir-fried vegetables with chapati", "Paneer tikka with salad"],
    "snack": ["Roasted chana", "Makhana", "Sprouts chaat", "Fruit with peanut butter", "Vegetable soup", "Buttermilk"],
}


@nutrition_bp.route("/nutrition")
@login_required
def nutrition():
    today = date.today()
    today_meals = MealLog.query.filter_by(user_id=current_user.id, date=today).all()
    today_calories = sum(m.calories or 0 for m in today_meals)
    today_protein = sum(m.protein_g or 0 for m in today_meals)
    today_carbs = sum(m.carbs_g or 0 for m in today_meals)
    today_fat = sum(m.fat_g or 0 for m in today_meals)

    client = get_watsonx_client()
    return render_template(
        "nutrition.html",
        today_meals=today_meals,
        today_calories=today_calories,
        today_protein=round(today_protein, 1),
        today_carbs=round(today_carbs, 1),
        today_fat=round(today_fat, 1),
        diet_types=DIET_TYPES,
        meal_types=MEAL_TYPES,
        indian_meals=INDIAN_MEALS,
        target_calories=current_user.tdee or 2000,
        ai_enabled=client is not None,
    )


@nutrition_bp.route("/api/generate-meal-plan", methods=["POST"])
@login_required
def generate_meal_plan():
    data = request.get_json(silent=True) or {}
    goal = data.get("goal", current_user.fitness_goal or "general fitness")
    diet_type = data.get("diet_type", current_user.dietary_preference or "vegetarian")
    calories = int(data.get("calories", current_user.tdee or 2000))
    days = int(data.get("days", 7))

    client = get_watsonx_client()
    if not client:
        return jsonify({"error": "AI service unavailable. Please configure watsonx.ai credentials."}), 503

    profile = current_user.to_profile_dict()
    plan = client.generate_meal_plan(profile, goal, calories, diet_type)
    return jsonify({"plan": plan})


@nutrition_bp.route("/api/nutrition-advice", methods=["POST"])
@login_required
def nutrition_advice():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Empty query"}), 400

    client = get_watsonx_client()
    if not client:
        return jsonify({"error": "AI service unavailable."}), 503

    profile = current_user.to_profile_dict()
    advice = client.chat([{"role": "user", "content": query}], user_profile=profile, max_tokens=800)
    return jsonify({"advice": advice})


@nutrition_bp.route("/api/meal-log", methods=["POST"])
@login_required
def log_meal():
    data = request.get_json(silent=True) or {}
    meal = MealLog(
        user_id=current_user.id,
        date=date.today(),
        meal_type=data.get("meal_type", "Snack"),
        food_item=data.get("food_item", ""),
        calories=data.get("calories", 0),
        protein_g=data.get("protein_g", 0),
        carbs_g=data.get("carbs_g", 0),
        fat_g=data.get("fat_g", 0),
    )
    db.session.add(meal)
    db.session.commit()
    return jsonify({"status": "logged", "meal": meal.to_dict()})


@nutrition_bp.route("/api/meal-log/<int:meal_id>", methods=["DELETE"])
@login_required
def delete_meal_log(meal_id):
    meal = MealLog.query.filter_by(id=meal_id, user_id=current_user.id).first_or_404()
    db.session.delete(meal)
    db.session.commit()
    return jsonify({"status": "deleted"})


@nutrition_bp.route("/api/nutrition-stats")
@login_required
def nutrition_stats():
    end = date.today()
    start = end - timedelta(days=6)
    logs = (
        MealLog.query.filter(
            MealLog.user_id == current_user.id,
            MealLog.date >= start,
            MealLog.date <= end,
        )
        .order_by(MealLog.date.asc())
        .all()
    )
    data = {}
    for log in logs:
        key = log.date.isoformat()
        if key not in data:
            data[key] = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
        data[key]["calories"] += log.calories or 0
        data[key]["protein"] += log.protein_g or 0
        data[key]["carbs"] += log.carbs_g or 0
        data[key]["fat"] += log.fat_g or 0

    labels, cal_data, prot_data, carb_data, fat_data = [], [], [], [], []
    current = start
    while current <= end:
        key = current.isoformat()
        labels.append(current.strftime("%a"))
        d = data.get(key, {})
        cal_data.append(round(d.get("calories", 0)))
        prot_data.append(round(d.get("protein", 0), 1))
        carb_data.append(round(d.get("carbs", 0), 1))
        fat_data.append(round(d.get("fat", 0), 1))
        current += timedelta(days=1)

    return jsonify({
        "labels": labels,
        "calories": cal_data,
        "protein": prot_data,
        "carbs": carb_data,
        "fat": fat_data,
    })
