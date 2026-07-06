"""
FitVerse — Fitness & Workout Routes
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import date, timedelta
from models import db, WorkoutLog
from watsonx_client import get_watsonx_client

fitness_bp = Blueprint("fitness", __name__)

WORKOUT_TYPES = [
    "Weight Loss", "Muscle Gain", "Strength Training", "Endurance",
    "Flexibility", "Yoga", "HIIT", "Home Workout", "Cardio",
    "Full Body", "Upper Body", "Lower Body", "Core", "Stretching"
]

FITNESS_LEVELS = ["Beginner", "Intermediate", "Advanced"]


@fitness_bp.route("/workout")
@login_required
def workout():
    today = date.today()
    recent_workouts = (
        WorkoutLog.query.filter_by(user_id=current_user.id)
        .order_by(WorkoutLog.date.desc())
        .limit(10)
        .all()
    )
    client = get_watsonx_client()
    return render_template(
        "workout.html",
        workout_types=WORKOUT_TYPES,
        fitness_levels=FITNESS_LEVELS,
        recent_workouts=recent_workouts,
        ai_enabled=client is not None,
        today=today,
    )


@fitness_bp.route("/api/generate-workout", methods=["POST"])
@login_required
def generate_workout():
    data = request.get_json(silent=True) or {}
    goal = data.get("goal", current_user.fitness_goal or "general fitness")
    level = data.get("level", current_user.fitness_level or "beginner")
    days = int(data.get("days", 3))
    equipment = data.get("equipment", current_user.equipment or "bodyweight")
    duration = int(data.get("duration", current_user.workout_time or 45))

    client = get_watsonx_client()
    if not client:
        return jsonify({"error": "AI service unavailable. Please configure watsonx.ai credentials."}), 503

    profile = current_user.to_profile_dict()
    profile.update({
        "equipment": equipment,
        "workout_time": duration,
        "fitness_level": level,
    })

    prompt = (
        f"Create a detailed {days}-day per week {level} workout plan for {goal}. "
        f"Equipment available: {equipment}. Session duration: {duration} minutes. "
        f"Include: warm-up (5 min), main workout with exercises/sets/reps/rest, "
        f"cool-down (5 min), and weekly schedule. Format with clear headings and emojis."
    )

    plan = client.chat(
        [{"role": "user", "content": prompt}],
        user_profile=profile,
        max_tokens=2000,
    )
    return jsonify({"plan": plan})


@fitness_bp.route("/api/workout-log", methods=["POST"])
@login_required
def log_workout():
    data = request.get_json(silent=True) or {}
    log = WorkoutLog(
        user_id=current_user.id,
        date=date.today(),
        workout_type=data.get("workout_type", "General"),
        duration_minutes=data.get("duration_minutes", 0),
        calories_burned=data.get("calories_burned", 0),
        notes=data.get("notes", ""),
        completed=True,
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"status": "logged", "log": log.to_dict()})


@fitness_bp.route("/api/workout-log/<int:log_id>", methods=["DELETE"])
@login_required
def delete_workout_log(log_id):
    log = WorkoutLog.query.filter_by(id=log_id, user_id=current_user.id).first_or_404()
    db.session.delete(log)
    db.session.commit()
    return jsonify({"status": "deleted"})


@fitness_bp.route("/api/workout-stats")
@login_required
def workout_stats():
    """Returns workout stats for the last 30 days for chart rendering."""
    end = date.today()
    start = end - timedelta(days=29)
    logs = (
        WorkoutLog.query.filter(
            WorkoutLog.user_id == current_user.id,
            WorkoutLog.date >= start,
            WorkoutLog.date <= end,
        )
        .order_by(WorkoutLog.date.asc())
        .all()
    )
    # Build daily data
    data = {}
    for log in logs:
        key = log.date.isoformat()
        if key not in data:
            data[key] = {"duration": 0, "calories": 0, "count": 0}
        data[key]["duration"] += log.duration_minutes or 0
        data[key]["calories"] += log.calories_burned or 0
        data[key]["count"] += 1

    labels = []
    durations = []
    calories = []
    current = start
    while current <= end:
        key = current.isoformat()
        labels.append(current.strftime("%b %d"))
        d = data.get(key, {})
        durations.append(d.get("duration", 0))
        calories.append(d.get("calories", 0))
        current += timedelta(days=1)

    total_workouts = sum(v["count"] for v in data.values())
    total_minutes = sum(v["duration"] for v in data.values())
    total_calories = sum(v["calories"] for v in data.values())

    return jsonify({
        "labels": labels,
        "durations": durations,
        "calories": calories,
        "total_workouts": total_workouts,
        "total_minutes": total_minutes,
        "total_calories": total_calories,
    })
