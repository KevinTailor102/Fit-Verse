"""
FitVerse — Tracker Routes (habits, water, sleep, BMI/BMR calculator)
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import date, timedelta
from models import db, HabitLog, WaterLog, SleepLog

tracker_bp = Blueprint("tracker", __name__)

DEFAULT_HABITS = [
    "Morning Workout",
    "Evening Walk",
    "Drink 8 Glasses of Water",
    "Eat Healthy Breakfast",
    "No Junk Food",
    "8 Hours of Sleep",
    "10-Minute Meditation",
    "Read / Learn Something New",
]


@tracker_bp.route("/tracker")
@login_required
def tracker():
    today = date.today()
    # Today's habits
    today_habits = HabitLog.query.filter_by(user_id=current_user.id, date=today).all()
    # Today's water
    today_water = WaterLog.query.filter_by(user_id=current_user.id, date=today).first()
    water_ml = today_water.amount_ml if today_water else 0
    # Today's sleep (last entry)
    last_sleep = (
        SleepLog.query.filter_by(user_id=current_user.id)
        .order_by(SleepLog.date.desc())
        .first()
    )
    # Weekly habit streak
    streak = _calculate_streak(current_user.id)

    return render_template(
        "tracker.html",
        today_habits=today_habits,
        default_habits=DEFAULT_HABITS,
        water_ml=water_ml,
        water_target_ml=current_user.weight * 35 if current_user.weight else 2500,
        last_sleep=last_sleep,
        streak=streak,
        today=today,
    )


def _calculate_streak(user_id: int) -> int:
    """Calculate the current daily habit completion streak."""
    streak = 0
    check_date = date.today()
    for _ in range(30):
        habits = HabitLog.query.filter_by(user_id=user_id, date=check_date).all()
        if habits and any(h.completed for h in habits):
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak


# ── Habit Endpoints ────────────────────────────────────────────────────────

@tracker_bp.route("/api/habit", methods=["POST"])
@login_required
def add_habit():
    data = request.get_json(silent=True) or {}
    habit_name = (data.get("habit_name") or "").strip()
    if not habit_name:
        return jsonify({"error": "Habit name required"}), 400

    existing = HabitLog.query.filter_by(
        user_id=current_user.id, date=date.today(), habit_name=habit_name
    ).first()
    if existing:
        return jsonify({"error": "Habit already added today"}), 409

    habit = HabitLog(
        user_id=current_user.id,
        date=date.today(),
        habit_name=habit_name,
        completed=False,
    )
    db.session.add(habit)
    db.session.commit()
    return jsonify({"status": "added", "habit": habit.to_dict()})


@tracker_bp.route("/api/habit/<int:habit_id>/toggle", methods=["POST"])
@login_required
def toggle_habit(habit_id):
    habit = HabitLog.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    habit.completed = not habit.completed
    db.session.commit()
    return jsonify({"status": "toggled", "completed": habit.completed})


@tracker_bp.route("/api/habit/<int:habit_id>", methods=["DELETE"])
@login_required
def delete_habit(habit_id):
    habit = HabitLog.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    db.session.delete(habit)
    db.session.commit()
    return jsonify({"status": "deleted"})


# ── Water Endpoints ───────────────────────────────────────────────────────

@tracker_bp.route("/api/water", methods=["POST"])
@login_required
def log_water():
    data = request.get_json(silent=True) or {}
    amount = int(data.get("amount_ml", 250))
    today = date.today()
    log = WaterLog.query.filter_by(user_id=current_user.id, date=today).first()
    if log:
        log.amount_ml += amount
    else:
        log = WaterLog(user_id=current_user.id, date=today, amount_ml=amount)
        db.session.add(log)
    db.session.commit()
    target = current_user.weight * 35 if current_user.weight else 2500
    return jsonify({"amount_ml": log.amount_ml, "target_ml": target})


@tracker_bp.route("/api/water/reset", methods=["POST"])
@login_required
def reset_water():
    log = WaterLog.query.filter_by(user_id=current_user.id, date=date.today()).first()
    if log:
        log.amount_ml = 0
        db.session.commit()
    return jsonify({"amount_ml": 0})


# ── Sleep Endpoints ───────────────────────────────────────────────────────

@tracker_bp.route("/api/sleep", methods=["POST"])
@login_required
def log_sleep():
    data = request.get_json(silent=True) or {}
    hours = float(data.get("hours", 7))
    quality = data.get("quality", "good")
    notes = data.get("notes", "")

    log = SleepLog(
        user_id=current_user.id,
        date=date.today(),
        hours=hours,
        quality=quality,
        notes=notes,
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"status": "logged", "sleep": log.to_dict()})


# ── Tracker Stats ─────────────────────────────────────────────────────────

@tracker_bp.route("/api/tracker-stats")
@login_required
def tracker_stats():
    end = date.today()
    start = end - timedelta(days=6)

    water_data = []
    habit_data = []
    sleep_data = []
    labels = []

    current = start
    while current <= end:
        labels.append(current.strftime("%a"))
        w = WaterLog.query.filter_by(user_id=current_user.id, date=current).first()
        water_data.append((w.amount_ml or 0) if w else 0)

        habits = HabitLog.query.filter_by(user_id=current_user.id, date=current).all()
        completed = sum(1 for h in habits if h.completed)
        total = len(habits)
        habit_data.append(round(completed / total * 100) if total > 0 else 0)

        s = (
            SleepLog.query.filter_by(user_id=current_user.id, date=current)
            .order_by(SleepLog.created_at.desc())
            .first()
        )
        sleep_data.append(s.hours if s else 0)

        current += timedelta(days=1)

    return jsonify({
        "labels": labels,
        "water": water_data,
        "habits": habit_data,
        "sleep": sleep_data,
    })


# ── BMI / BMR Calculator ─────────────────────────────────────────────────

@tracker_bp.route("/api/calculate-bmi-bmr", methods=["POST"])
def calculate_bmi_bmr():
    data = request.get_json(silent=True) or {}
    weight = float(data.get("weight", 0))
    height = float(data.get("height", 0))
    age = int(data.get("age", 0))
    gender = data.get("gender", "male")
    activity = data.get("activity_level", "sedentary")

    if not (weight and height and age):
        return jsonify({"error": "Weight, height, and age are required"}), 400

    h_m = height / 100
    bmi = round(weight / (h_m * h_m), 1)

    if bmi < 18.5:
        bmi_cat = "Underweight"
        bmi_color = "#3b82d4"
    elif bmi < 25:
        bmi_cat = "Normal Weight"
        bmi_color = "#22c55e"
    elif bmi < 30:
        bmi_cat = "Overweight"
        bmi_color = "#f59e0b"
    else:
        bmi_cat = "Obese"
        bmi_color = "#ef4444"

    # Mifflin-St Jeor BMR
    if gender == "male":
        bmr = round(10 * weight + 6.25 * height - 5 * age + 5, 1)
    else:
        bmr = round(10 * weight + 6.25 * height - 5 * age - 161, 1)

    multipliers = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9,
    }
    tdee = round(bmr * multipliers.get(activity, 1.2), 1)

    ideal_weight_low = round(18.5 * h_m * h_m, 1)
    ideal_weight_high = round(24.9 * h_m * h_m, 1)

    return jsonify({
        "bmi": bmi,
        "bmi_category": bmi_cat,
        "bmi_color": bmi_color,
        "bmr": bmr,
        "tdee": tdee,
        "ideal_weight_low": ideal_weight_low,
        "ideal_weight_high": ideal_weight_high,
        "weight_loss_calories": tdee - 500,
        "weight_gain_calories": tdee + 500,
        "maintenance_calories": tdee,
        "water_intake_ml": round(weight * 35),
        "protein_target_g": round(weight * 1.8),
    })
