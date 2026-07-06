"""
FitVerse — Main Routes (dashboard, profile, calculator)
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import date, timedelta
from models import db, User, WorkoutLog, MealLog, WaterLog, SleepLog, HabitLog

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Today's summary
    today_workouts = WorkoutLog.query.filter_by(user_id=current_user.id, date=today).all()
    today_meals = MealLog.query.filter_by(user_id=current_user.id, date=today).all()
    today_water = WaterLog.query.filter_by(user_id=current_user.id, date=today).first()
    today_habits = HabitLog.query.filter_by(user_id=current_user.id, date=today).all()

    # Weekly stats
    weekly_workouts = WorkoutLog.query.filter(
        WorkoutLog.user_id == current_user.id,
        WorkoutLog.date >= week_start,
    ).count()

    total_calories_today = sum(m.calories or 0 for m in today_meals)
    total_workout_mins = sum(w.duration_minutes or 0 for w in today_workouts)
    water_ml = today_water.amount_ml if today_water else 0
    habits_done = sum(1 for h in today_habits if h.completed)
    habits_total = len(today_habits)

    # Last 7-day workout data for mini chart
    chart_labels, chart_data = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        logs = WorkoutLog.query.filter_by(user_id=current_user.id, date=d).all()
        chart_labels.append(d.strftime("%a"))
        chart_data.append(sum(l.duration_minutes or 0 for l in logs))

    return render_template(
        "dashboard.html",
        today=today,
        weekly_workouts=weekly_workouts,
        total_calories_today=total_calories_today,
        total_workout_mins=total_workout_mins,
        water_ml=water_ml,
        water_target=current_user.weight * 35 if current_user.weight else 2500,
        habits_done=habits_done,
        habits_total=habits_total,
        today_workouts=today_workouts,
        today_meals=today_meals[:5],
        chart_labels=chart_labels,
        chart_data=chart_data,
        target_calories=current_user.tdee or 2000,
    )


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", "").strip()
        current_user.age = _safe_int(request.form.get("age"))
        current_user.gender = request.form.get("gender")
        current_user.weight = _safe_float(request.form.get("weight"))
        current_user.height = _safe_float(request.form.get("height"))
        current_user.fitness_goal = request.form.get("fitness_goal")
        current_user.activity_level = request.form.get("activity_level")
        current_user.dietary_preference = request.form.get("dietary_preference")
        current_user.equipment = request.form.get("equipment")
        current_user.workout_time = _safe_int(request.form.get("workout_time")) or 45
        current_user.fitness_level = request.form.get("fitness_level", "beginner")

        db.session.commit()
        flash("Profile updated successfully! 🎯", "success")
        return redirect(url_for("main.profile"))

    return render_template("profile.html")


@main_bp.route("/calculator")
@login_required
def calculator():
    return render_template("calculator.html")


def _safe_int(val):
    try:
        return int(val) if val else None
    except (ValueError, TypeError):
        return None


def _safe_float(val):
    try:
        return float(val) if val else None
    except (ValueError, TypeError):
        return None
