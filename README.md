## FitVerse — AI-Powered Fitness Web Application

<div align="center">
  <img src="https://img.shields.io/badge/IBM%20watsonx.ai-Granite-0066CC?style=for-the-badge&logo=ibm" />
  <img src="https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap" />
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite" />
</div>

---

FitVerse is a full-stack AI fitness coaching web application powered by **IBM watsonx.ai Granite** models. It delivers personalized workout plans, nutrition advice, BMI/BMR analysis, habit tracking, and an interactive ChatGPT-style fitness coach — all in a modern, responsive interface with dark mode support.

---

## Features

| Feature | Description |
|---|---|
| 🤖 AI Chat Coach | IBM Granite-powered conversational fitness coach with full conversation history |
| 💪 Workout Planner | AI-generated beginner/intermediate/advanced plans for 14+ workout types |
| 🥗 Nutrition Planner | Personalized Indian & international meal plans with macro tracking |
| 📊 BMI & BMR Calculator | Health metrics with macro distribution pie chart |
| 📈 Progress Dashboard | Weekly activity charts, calorie tracking, goal visualization |
| ✅ Habit Tracker | Daily habits, water intake tracker, sleep logger |
| 👤 Profile Management | Full fitness profile with BMI/TDEE auto-calculation |
| 🌙 Dark Mode | Smooth light/dark toggle with localStorage persistence |
| 📱 Mobile Responsive | Collapsible sidebar, touch-friendly UI |

---

## Tech Stack

- **Backend**: Python 3.11+, Flask 3.0, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt
- **AI**: IBM watsonx.ai SDK, IBM Granite 13B Chat v2
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Bootstrap 5.3, Chart.js 4, Font Awesome 6, Inter font
- **Auth**: Session-based authentication with bcrypt password hashing

---

## Project Structure

```
FitVerse/
├── app.py                    # Flask application factory & entry point
├── config.py                 # Environment-based configuration
├── models.py                 # SQLAlchemy database models
├── watsonx_client.py         # IBM watsonx.ai Granite API client
├── agent_instructions.py     # 🎛️ AI coach customization (edit this!)
├── requirements.txt
├── .env.example
├── routes/
│   ├── auth.py               # Login, register, logout
│   ├── main.py               # Dashboard, profile, calculator
│   ├── chat.py               # AI chat API endpoints
│   ├── fitness.py            # Workout planner & logging
│   ├── nutrition.py          # Meal planner & logging
│   └── tracker.py            # Habits, water, sleep, BMI API
├── templates/
│   ├── base.html             # Sidebar layout base
│   ├── index.html            # Landing page
│   ├── dashboard.html        # Main dashboard
│   ├── chat.html             # AI chat interface
│   ├── workout.html          # Workout planner
│   ├── nutrition.html        # Nutrition planner
│   ├── calculator.html       # BMI/BMR calculator
│   ├── tracker.html          # Habit tracker
│   ├── profile.html          # User profile editor
│   └── auth/
│       ├── login.html
│       └── register.html
└── static/
    ├── css/style.css         # Complete custom stylesheet
    └── js/app.js             # Dark mode, sidebar, toast utils
```

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- IBM Cloud account with watsonx.ai access
- IBM Cloud API Key
- watsonx.ai Project ID

### 1. Clone & Install

```bash
git clone https://github.com/your-username/fitverse.git
cd fitverse
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=1

WATSONX_API_KEY=your-ibm-cloud-api-key
WATSONX_PROJECT_ID=your-watsonx-project-id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-13b-chat-v2
```

### 3. Run the Application

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

The SQLite database (`fitverse.db`) is created automatically on first run.

---

## Getting IBM watsonx.ai Credentials

1. Sign up at [IBM Cloud](https://cloud.ibm.com)
2. Navigate to **AI / Machine Learning → watsonx.ai**
3. Create a new **Project**
4. Go to **Project Settings → General** → copy the **Project ID**
5. Go to **Manage → Access (IAM) → API Keys** → create a new API key
6. Set `WATSONX_API_KEY` and `WATSONX_PROJECT_ID` in your `.env`

> **Model**: The default model is `ibm/granite-13b-chat-v2`. You can also use `ibm/granite-7b-lab` or `ibm/granite-20b-multilingual`.

---

## Customizing the AI Coach

Edit `agent_instructions.py` to change the AI's behavior:

```python
# Change the coach's name
COACH_NAME = "FitBot"

# Adjust personality and tone
COACH_PERSONA = "..."

# Modify workout intensity guidelines
WORKOUT_INTENSITY = "..."

# Change nutrition preferences (Indian diet, vegan, etc.)
NUTRITION_PREFERENCES = "..."

# Update safety guidelines
SAFETY_GUIDELINES = "..."
```

These changes take effect immediately without restarting the server.

---

## Deployment

### Option 1: Local Production with Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:app"
```

### Option 2: IBM Cloud Code Engine

#### Prerequisites
- IBM Cloud CLI installed
- Code Engine CLI plugin

```bash
# Install IBM Cloud CLI
curl -fsSL https://clis.cloud.ibm.com/install/linux | sh
ibmcloud plugin install code-engine

# Login
ibmcloud login --apikey YOUR_IBM_CLOUD_API_KEY -r us-south
ibmcloud target -g Default

# Create Code Engine project
ibmcloud ce project create --name fitverse-project
ibmcloud ce project select --name fitverse-project

# Deploy from local source (builds automatically)
ibmcloud ce app create \
  --name fitverse \
  --build-source . \
  --build-strategy buildpacks \
  --port 5000 \
  --env WATSONX_API_KEY=your-api-key \
  --env WATSONX_PROJECT_ID=your-project-id \
  --env SECRET_KEY=your-secret-key \
  --env FLASK_ENV=production \
  --min-scale 0 \
  --max-scale 3

# Get the app URL
ibmcloud ce app get --name fitverse --output url
```

#### Using a Procfile (for buildpacks)

Create `Procfile` in the project root:
```
web: gunicorn -w 2 -b 0.0.0.0:$PORT "app:app"
```

### Option 3: Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t fitverse .
docker run -p 5000:5000 --env-file .env fitverse
```

### Option 4: Railway / Render / Heroku

1. Push code to GitHub
2. Connect your GitHub repo to Railway/Render
3. Set environment variables in the dashboard
4. Deploy — the platform detects Flask automatically

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ Yes | Flask session secret key |
| `WATSONX_API_KEY` | ✅ Yes | IBM Cloud API Key |
| `WATSONX_PROJECT_ID` | ✅ Yes | watsonx.ai Project ID |
| `WATSONX_URL` | No | watsonx.ai endpoint (default: us-south) |
| `WATSONX_MODEL_ID` | No | Granite model ID (default: granite-13b-chat-v2) |
| `FLASK_ENV` | No | development or production |
| `DATABASE_URL` | No | SQLite path or PostgreSQL URL |

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/chat` | POST | Send message to AI coach |
| `/api/chat/history` | GET | Get conversation history |
| `/api/generate-workout` | POST | Generate AI workout plan |
| `/api/workout-log` | POST | Log a workout |
| `/api/workout-stats` | GET | 30-day workout statistics |
| `/api/generate-meal-plan` | POST | Generate AI meal plan |
| `/api/meal-log` | POST | Log a meal |
| `/api/nutrition-stats` | GET | 7-day nutrition statistics |
| `/api/calculate-bmi-bmr` | POST | Calculate BMI/BMR/TDEE |
| `/api/habit` | POST | Add a daily habit |
| `/api/habit/<id>/toggle` | POST | Toggle habit completion |
| `/api/water` | POST | Log water intake |
| `/api/sleep` | POST | Log sleep hours |
| `/api/tracker-stats` | GET | 7-day tracker statistics |

---

## Screenshots

The application includes:
- **Landing page** with hero section and feature highlights
- **Dashboard** with stat cards and weekly activity chart
- **ChatGPT-style AI chat** with typing animation and quick action buttons
- **Workout planner** with AI generation form and workout history table
- **Nutrition planner** with Indian meal suggestions and macro chart
- **BMI/BMR calculator** with macro distribution doughnut chart
- **Habit tracker** with water progress bar and 7-day charts
- **Profile editor** with live BMI/TDEE display

---

## Security Notes

- Passwords are hashed with bcrypt (12 rounds)
- Sessions use httponly cookies
- Never commit `.env` to version control — it's in `.gitignore`
- For production, set `SESSION_COOKIE_SECURE=True` and use HTTPS
- The watsonx.ai API key is never exposed to the frontend

---

## License

MIT License — free for personal and commercial use.

---

<div align="center">
  Built with ❤️ using <strong>IBM watsonx.ai Granite</strong> · Flask · Bootstrap 5
</div>
