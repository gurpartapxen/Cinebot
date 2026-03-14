from app.services.tmdb import TMDBService, GENRE_MAP, MOOD_TO_GENRE


class RecommenderService:
    """
    Personalized recommendation engine.
    Tracks user genre preferences from chat history
    and scores movies based on their taste profile.
    """

    def __init__(self):
        self.tmdb = TMDBService()

    # ── Build a taste profile from chat history ──────────────────────────
    def build_profile(self, chat_history):
        """
        Analyses past messages to build a genre preference score dict.
        Returns e.g. {'thriller': 3, 'sci-fi': 2, 'horror': 1}
        """
        profile = {}

        genre_keywords = {
            'thriller':    ['thriller', 'suspense', 'tense', 'mystery', 'detective'],
            'horror':      ['horror', 'scary', 'terrifying', 'ghost', 'slasher', 'fear'],
            'comedy':      ['comedy', 'funny', 'laugh', 'hilarious', 'humor', 'lighthearted'],
            'romance':     ['romance', 'romantic', 'love', 'relationship', 'heartwarming'],
            'action':      ['action', 'fight', 'explosion', 'adventure', 'hero'],
            'sci-fi':      ['sci-fi', 'science fiction', 'space', 'future', 'alien', 'robot'],
            'drama':       ['drama', 'emotional', 'moving', 'touching', 'deep', 'meaningful'],
            'animation':   ['animation', 'animated', 'cartoon', 'pixar', 'disney'],
            'documentary': ['documentary', 'real', 'true story', 'based on'],
            'crime':       ['crime', 'mafia', 'gangster', 'heist', 'murder'],
            'fantasy':     ['fantasy', 'magic', 'wizard', 'mythical', 'dragon'],
        }

        mood_keywords = {
            'happy':       ['happy', 'cheerful', 'fun', 'upbeat', 'joyful'],
            'sad':         ['sad', 'cry', 'emotional', 'depressing', 'melancholy'],
            'excited':     ['excited', 'thrilling', 'adrenaline', 'intense', 'edge of seat'],
            'relaxed':     ['relaxed', 'chill', 'easy', 'light', 'calm'],
            'adventurous': ['adventure', 'explore', 'journey', 'quest'],
        }

        for msg in chat_history:
            if not msg:
                continue
            text = msg.lower()

            # Score genres
            for genre, keywords in genre_keywords.items():
                for kw in keywords:
                    if kw in text:
                        profile[genre] = profile.get(genre, 0) + 1

            # Score moods → translate to genres
            for mood, keywords in mood_keywords.items():
                for kw in keywords:
                    if kw in text:
                        mood_genres = MOOD_TO_GENRE.get(mood, [])
                        for g in mood_genres:
                            profile[g] = profile.get(g, 0) + 0.5

        return profile

    # ── Get top genre from profile ────────────────────────────────────────
    def top_genre(self, profile):
        if not profile:
            return None
        return max(profile, key=profile.get)

    # ── Score a list of movies against a profile ──────────────────────────
    def score_movies(self, movies, profile):
        """
        Adds a 'score' key to each movie based on how well
        it matches the user's genre preference profile.
        """
        scored = []
        for m in movies:
            score = float(m.get('rating', 0))
            genre_ids = m.get('genre_ids', [])

            # Map genre IDs back to genre names and score
            id_to_name = {v: k for k, v in GENRE_MAP.items()}
            for gid in genre_ids:
                gname = id_to_name.get(gid)
                if gname and gname in profile:
                    score += profile[gname] * 2

            m['score'] = round(score, 2)
            scored.append(m)

        return sorted(scored, key=lambda x: x['score'], reverse=True)

    # ── Main: get personalised recommendations ────────────────────────────
    def get_recommendations(self, chat_history, limit=5):
        """
        Main method — call this from chatbot.py to get
        personalised movie picks based on conversation history.
        """
        profile = self.build_profile(chat_history)

        if not profile:
            # No taste profile yet — return popular movies
            return self.tmdb.get_popular()[:limit]

        top = self.top_genre(profile)
        genre_id = GENRE_MAP.get(top)

        if genre_id:
            movies = self.tmdb.get_by_genre(genre_id)
        else:
            movies = self.tmdb.get_popular()

        # Blend with popular to add variety
        popular = self.tmdb.get_popular()
        blended = {m['title']: m for m in (movies + popular)}.values()

        scored = self.score_movies(list(blended), profile)
        return scored[:limit]

    # ── Get "because you liked X" recommendations ─────────────────────────
    def get_similar(self, movie_title, limit=4):
        """
        Returns movies similar to a given title
        by searching TMDB and fetching related content.
        """
        results = self.tmdb.search_movies(movie_title)
        if not results:
            return []

        # Use genres of the first result to find similar
        top_result  = results[0]
        genre_ids   = top_result.get('genre_ids', [])
        id_to_name  = {v: k for k, v in GENRE_MAP.items()}

        similar = []
        for gid in genre_ids[:2]:
            gname = id_to_name.get(gid)
            if gname:
                movies = self.tmdb.get_by_genre(gid)
                similar.extend(movies)

        # Remove the original movie from results
        similar = [m for m in similar if m['title'].lower() != movie_title.lower()]

        # Deduplicate
        seen   = set()
        unique = []
        for m in similar:
            if m['title'] not in seen:
                seen.add(m['title'])
                unique.append(m)

        return unique[:limit]