"""
FitVerse — SQLAlchemy Database Models
"""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    """Application user with fitness profile."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Profile
    full_name = db.Column(db.String(120))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))          # male / female / other
    weight = db.Column(db.Float)               # kg
    height = db.Column(db.Float)               # cm
    fitness_goal = db.Column(db.String(60))    # weight_loss / muscle_gain / strength / endurance / flexibility / general
    activity_level = db.Column(db.String(40))  # sedentary / lightly_active / moderately_active / very_active / extra_active
    dietary_preference = db.Column(db.String(40))  # vegetarian / vegan / non_vegetarian / high_protein
    equipment = db.Column(db.String(100))      # comma-separated: bodyweight, dumbbells, barbell, gym, resistance_bands
    workout_time = db.Column(db.Integer, default=45)  # minutes per session
    fitness_level = db.Column(db.String(20), default="beginner")  # beginner / intermediate / advanced
    avatar_color = db.Column(db.String(10), default="#3b82d4")

    # Relationships
    chat_messages = db.relationship("ChatMessage", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    workouts = db.relationship("WorkoutLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    meals = db.relationship("MealLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    habits = db.relationship("HabitLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    water_logs = db.relationship("WaterLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    sleep_logs = db.relationship("SleepLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def bmi(self) -> float | None:
        if self.weight and self.height:
            h_m = self.height / 100
            return round(self.weight / (h_m * h_m), 1)
        return None

    @property
    def bmi_category(self) -> str:
        b = self.bmi
        if b is None:
            return "Unknown"
        if b < 18.5:
            return "Underweight"
        if b < 25:
            return "Normal"
        if b < 30:
            return "Overweight"
        return "Obese"

    @property
    def bmr(self) -> float | None:
        """Mifflin-St Jeor BMR."""
        if not (self.weight and self.height and self.age and self.gender):
            return None
        if self.gender == "male":
            return round(10 * self.weight + 6.25 * self.height - 5 * self.age + 5, 1)
        return round(10 * self.weight + 6.25 * self.height - 5 * self.age - 161, 1)

    @property
    def tdee(self) -> float | None:
        """Total Daily Energy Expenditure."""
        b = self.bmr
        if b is None:
            return None
        multipliers = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extra_active": 1.9,
        }
        m = multipliers.get(self.activity_level or "sedentary", 1.2)
        return round(b * m, 1)

    def to_profile_dict(self) -> dict:
        return {
            "name": self.full_name or self.username,
            "age": self.age,
            "gender": self.gender,
            "weight": self.weight,
            "height": self.height,
            "bmi": self.bmi,
            "bmi_category": self.bmi_category,
            "bmr": self.bmr,
            "tdee": self.tdee,
            "goal": self.fitness_goal,
            "activity_level": self.activity_level,
            "dietary_preference": self.dietary_preference,
            "equipment": self.equipment,
            "workout_time": self.workout_time,
            "fitness_level": self.fitness_level,
        }

    def __repr__(self):
        return f"<User {self.username}>"


class ChatMessage(db.Model):
    """Stores the chat conversation history per user."""
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False)   # user | assistant
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }


class WorkoutLog(db.Model):
    """Tracks completed workout sessions."""
    __tablename__ = "workout_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, default=date.today)
    workout_type = db.Column(db.String(60))
    duration_minutes = db.Column(db.Integer)
    calories_burned = db.Column(db.Integer)
    notes = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "workout_type": self.workout_type,
            "duration_minutes": self.duration_minutes,
            "calories_burned": self.calories_burned,
            "notes": self.notes,
            "completed": self.completed,
        }


class MealLog(db.Model):
    """Tracks meals and calorie intake."""
    __tablename__ = "meal_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, default=date.today)
    meal_type = db.Column(db.String(30))   # breakfast / lunch / dinner / snack
    food_item = db.Column(db.String(200))
    calories = db.Column(db.Integer)
    protein_g = db.Column(db.Float)
    carbs_g = db.Column(db.Float)
    fat_g = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "meal_type": self.meal_type,
            "food_item": self.food_item,
            "calories": self.calories,
            "protein_g": self.protein_g,
            "carbs_g": self.carbs_g,
            "fat_g": self.fat_g,
        }


class HabitLog(db.Model):
    """Daily habit tracking (workout, water, sleep, nutrition)."""
    __tablename__ = "habit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, default=date.today)
    habit_name = db.Column(db.String(100))
    completed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "habit_name": self.habit_name,
            "completed": self.completed,
            "notes": self.notes,
        }


class WaterLog(db.Model):
    """Daily water intake log."""
    __tablename__ = "water_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, default=date.today)
    amount_ml = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "amount_ml": self.amount_ml,
        }


class SleepLog(db.Model):
    """Daily sleep tracking."""
    __tablename__ = "sleep_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, default=date.today)
    hours = db.Column(db.Float)
    quality = db.Column(db.String(20))   # poor / fair / good / excellent
    notes = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "hours": self.hours,
            "quality": self.quality,
            "notes": self.notes,
        }
