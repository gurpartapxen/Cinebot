import os
os.environ.pop('GOOGLE_API_KEY', None)

from google import genai
from flask import current_app
from app.services.tmdb import TMDBService, MOOD_TO_GENRE, GENRE_MAP
from app.services.recommender import RecommenderService

SYSTEM_INSTRUCTION = """You are CineBot, an expert AI movie and TV show companion.
Help users discover movies and shows they will love.

Rules:
- Recommend based on mood, genre, or description
- Never spoil plots unless the user explicitly asks
- Remember context from earlier in the conversation
- Ask follow-up questions to understand taste better
- Always mention title, year, and why the user will enjoy it
- Keep responses under 150 words, friendly and conversational
- If user mentions a mood (happy, sad, excited, scared, romantic, curious, adventurous, relaxed, bored) tailor recommendations to it
- Do not use emojis in your responses
- Format movie titles in bold using **title** syntax"""


class ChatbotService:
    def __init__(self, session_id):
        self.session_id       = session_id
        self.tmdb             = TMDBService()
        self.recommender      = RecommenderService()
        self.history_messages = []

        os.environ.pop('GOOGLE_API_KEY', None)
        self.client = genai.Client(
            api_key=current_app.config['GEMINI_API_KEY']
        )
        self.conversation = self.client.chats.create(
            model="gemini-2.5-flash",
            config={"system_instruction": SYSTEM_INSTRUCTION}
        )

    def detect_intent(self, message):
        msg = message.lower()
        for mood in MOOD_TO_GENRE.keys():
            if mood in msg:
                return f'mood:{mood}'
        if any(w in msg for w in ['recommend', 'suggest', 'what should', 'find me', 'give me', 'show me', 'list']):
            return 'recommend'
        if any(w in msg for w in ['search', 'look up', 'find', 'about']):
            return 'search'
        if any(w in msg for w in ['popular', 'trending', 'best', 'top', 'latest', 'new']):
            return 'popular'
        if any(w in msg for w in ['thriller', 'horror', 'comedy', 'drama', 'action', 'romance', 'sci-fi', 'fantasy', 'mystery', 'crime', 'documentary']):
            return 'recommend'
        return 'chat'

    def get_movies(self, message, intent):
        try:
            if intent == 'popular':
                return self.tmdb.get_popular()
            if intent.startswith('mood:'):
                mood     = intent.split(':')[1]
                genres   = MOOD_TO_GENRE.get(mood, ['drama'])
                genre_id = GENRE_MAP.get(genres[0], 18)
                return self.tmdb.get_by_genre(genre_id)
            if intent in ['recommend', 'search']:
                msg = message.lower()
                for genre, gid in GENRE_MAP.items():
                    if genre in msg:
                        return self.tmdb.get_by_genre(gid)
                words = [w for w in message.split() if len(w) > 3]
                query = ' '.join(words[:4])
                if query:
                    return self.tmdb.search_movies(query)
        except Exception:
            pass
        return []

    def respond(self, user_message):
        self.history_messages.append(user_message)
        intent = self.detect_intent(user_message)
        msg    = user_message.lower()

        # Personalised recommendations after enough history
        if intent in ['recommend', 'popular'] and len(self.history_messages) > 2:
            movies = self.recommender.get_recommendations(self.history_messages)

        # Similar movie detection
        elif 'similar to' in msg or ('like' in msg and any(
            w in msg for w in ['something', 'movies', 'films', 'show']
        )):
            query  = msg.replace('similar to', '').replace('something like', '').replace('movies like', '').replace('films like', '').strip()
            movies = self.recommender.get_similar(query) or self.get_movies(user_message, intent)

        else:
            movies = self.get_movies(user_message, intent)

        context = ''
        if movies:
            titles  = ', '.join([f"{m['title']} ({m['year']}, {m['rating']}/10)" for m in movies[:4]])
            context = f' [Relevant movies from database: {titles}]'

        response = self.conversation.send_message(user_message + context)
        self.history_messages.append(response.text)

        return {
            'message': response.text,
            'movies':  movies[:4] if movies else []
        }