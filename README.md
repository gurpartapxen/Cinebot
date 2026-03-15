🎬 CineBot — AI Movie Companion

An intelligent movie discovery platform powered by Google Gemini AI, built with Flask and deployed on Railway.

Live Demo: [cinebot-hype.up.railway.app](https://cinebot-hype.up.railway.app)

# Features

 AI Chat — Conversational movie recommendations powered by Google Gemini 2.5 Flash with memory
 Discover — Browse 60+ movies across 5 tabs (Popular, Top Rated, Trending, Upcoming, Now Playing) with genre filters
 Search — Real-time movie search with instant results
 Streaming — Browse 10 platforms (Netflix, Prime, Disney+, Hotstar, JioCinema etc.) and see where any movie is streaming
 Watchlist & Ratings— Save movies and rate them out of 10
 Reviews— Write and like movie reviews
 Social — Add friends, see their activity feed, send/accept friend requests
 Dark/Light Mode — Persisted across sessions
 Background Collage** — Dynamic movie poster backgrounds

#Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask |
| Database | MySQL + SQLAlchemy ORM |
| AI | Google Gemini 2.5 Flash |
| Movie Data | TMDB API |
| Auth | Flask-Login + Bcrypt |
| Frontend | Jinja2, Vanilla JS, Custom CSS |
| Fonts | Clash Display, Cabinet Grotesk |
| Deployment | Railway (App + MySQL) |

--Getting Started

#Prerequisites
- Python 3.11+
- MySQL
- TMDB API Key — [Get one free](https://www.themoviedb.org/settings/api)
- Google Gemini API Key — [Get one free](https://aistudio.google.com)

#Local Setup

**1. Clone the repo**
```bash
git clone https://github.com/gurpartapxen/Cinebot.git
cd Cinebot


**2. Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux


**3. Install dependencies**
```bash
pip install -r requirements.txt


**4. Set up MySQL database**
```sql
CREATE DATABASE movie_chatbot_db;
CREATE USER 'chatbot_user'@'localhost' IDENTIFIED BY 'chatbot123';
GRANT ALL PRIVILEGES ON movie_chatbot_db.* TO 'chatbot_user'@'localhost';
FLUSH PRIVILEGES;


**5. Create `.env` file in project root**

GEMINI_API_KEY=your_gemini_api_key
TMDB_API_KEY=your_tmdb_api_key
SECRET_KEY=your_secret_key
DATABASE_URL=mysql+pymysql://chatbot_user:chatbot123@localhost/movie_chatbot_db

**6. Run the app**
```bash
python run.py

Visit `http://localhost:5000` 

#Project Structure

---
CineBot/
├── app/
│   ├── __init__.py           # App factory, blueprint registration
│   ├── models.py             # SQLAlchemy models
│   ├── routes/
│   │   ├── auth.py           # Register, login, logout
│   │   ├── chat.py           # AI chat API, watchlist, ratings
│   │   ├── discover.py       # Movie discovery, search
│   │   ├── profile.py        # User profile
│   │   ├── social.py         # Friends, activity feed
│   │   └── streaming.py      # Streaming platform browser
│   ├── services/
│   │   ├── chatbot.py        # Gemini AI integration
│   │   ├── tmdb.py           # TMDB API service
│   │   └── recommender.py    # Personalised recommendations
│   ├── templates/            # Jinja2 HTML templates
│   └── static/               # CSS, JS assets
├── config.py                 # Configuration
├── run.py                    # App entry point
├── requirements.txt
├── Procfile                  # Railway deployment
└── runtime.txt
```

---

## 🗄 Database Schema

| Table | Description |
|-------|-------------|
| `users` | User accounts with auth |
| `watch_history` | Movies watched by users |
| `watchlist` | Saved movies |
| `movie_ratings` | User ratings (1-10) |
| `movie_reviews` | Written reviews with likes |
| `chat_sessions` | AI chat history |
| `friendships` | Friend connections |
| `activity_feed` | Social activity log |

---

#Deployment

Deployed on Railway with a managed MySQL database.

**Environment Variables Required:**
```
DATABASE_URL    = mysql+pymysql://...   (Railway MySQL internal URL)
GEMINI_API_KEY  = AIza...
TMDB_API_KEY    = ...
SECRET_KEY      = ...
FLASK_ENV       = production
```

#Key Features Deep Dive

# AI Chat
Powered by Google Gemini 2.5 Flash. The chatbot understands natural language queries like *"suggest a thriller like Inception"* or *"what should I watch on a rainy day"* and responds with personalised movie recommendations based on your watch history.

# Streaming Discovery
Uses TMDB's Watch Providers API to show which platforms (Netflix, Prime Video, Disney+, Hotstar, JioCinema, SonyLIV etc.) are streaming any movie. Clicking a platform shows all movies available on it, filtered by region.

#Social Features
Add friends, see their ratings and reviews in a live activity feed, and discover movies through social recommendations.

📄 License

MIT License — feel free to use this project for learning and portfolio purposes.

👨‍💻 Author

Gurpartap — Final Year Computer Science Project
