"""
FitVerse — Chat Routes (AI fitness coach powered by IBM watsonx.ai Granite)
"""
import json
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, ChatMessage
from watsonx_client import get_watsonx_client

chat_bp = Blueprint("chat", __name__)

QUICK_ACTIONS = [
    {"icon": "💪", "label": "Workout Plan", "prompt": "Create a personalized workout plan for me based on my profile."},
    {"icon": "🥗", "label": "Meal Plan", "prompt": "Generate a 7-day meal plan suited to my fitness goals and dietary preferences."},
    {"icon": "🔥", "label": "Calorie Target", "prompt": "What should my daily calorie intake be to reach my fitness goal?"},
    {"icon": "🧘", "label": "Yoga Routine", "prompt": "Suggest a beginner yoga routine I can do at home."},
    {"icon": "🏃", "label": "HIIT Workout", "prompt": "Give me a 20-minute HIIT workout I can do at home without equipment."},
    {"icon": "😴", "label": "Recovery Tips", "prompt": "What are the best recovery tips after an intense workout?"},
    {"icon": "💧", "label": "Hydration Guide", "prompt": "How much water should I drink daily and what are the best hydration strategies?"},
    {"icon": "🥑", "label": "Indian Diet Tips", "prompt": "Give me healthy Indian diet tips and meal suggestions for my fitness goal."},
]


@chat_bp.route("/chat")
@login_required
def chat():
    messages = (
        ChatMessage.query.filter_by(user_id=current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(50)
        .all()
    )
    messages.reverse()
    client = get_watsonx_client()
    return render_template(
        "chat.html",
        messages=messages,
        quick_actions=QUICK_ACTIONS,
        ai_enabled=client is not None,
    )


@chat_bp.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    clear = data.get("clear", False)

    if clear:
        ChatMessage.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({"status": "cleared"})

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    if len(user_message) > 2000:
        return jsonify({"error": "Message too long (max 2000 characters)"}), 400

    # Save user message
    user_msg = ChatMessage(user_id=current_user.id, role="user", content=user_message)
    db.session.add(user_msg)
    db.session.commit()

    # Build conversation history (last 20 messages for context window)
    history = (
        ChatMessage.query.filter_by(user_id=current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )
    history.reverse()
    messages = [{"role": m.role, "content": m.content} for m in history]

    client = get_watsonx_client()
    if client:
        profile = current_user.to_profile_dict()
        reply = client.chat(messages, user_profile=profile)
    else:
        reply = (
            "⚠️ AI features are currently unavailable. Please configure your IBM watsonx.ai "
            "API key and Project ID in the `.env` file to enable the AI fitness coach.\n\n"
            "In the meantime, explore the Workout Planner, Nutrition Planner, and Trackers!"
        )

    # Save assistant reply
    bot_msg = ChatMessage(user_id=current_user.id, role="assistant", content=reply)
    db.session.add(bot_msg)
    db.session.commit()

    return jsonify({
        "reply": reply,
        "message_id": bot_msg.id,
        "timestamp": bot_msg.created_at.strftime("%H:%M"),
    })


@chat_bp.route("/api/chat/history")
@login_required
def chat_history():
    messages = (
        ChatMessage.query.filter_by(user_id=current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return jsonify([m.to_dict() for m in messages])


@chat_bp.route("/api/fitness-tip")
@login_required
def fitness_tip():
    client = get_watsonx_client()
    if not client:
        tips = [
            "💧 Drink a glass of water first thing in the morning!",
            "🚶 Take a 10-minute walk after every meal.",
            "🥗 Include protein in every meal to stay full longer.",
            "😴 Quality sleep is as important as your workout.",
            "🧘 5 minutes of stretching daily prevents injury.",
        ]
        import random
        return jsonify({"tip": random.choice(tips)})

    profile = current_user.to_profile_dict()
    tip = client.get_fitness_tip(profile)
    return jsonify({"tip": tip})
