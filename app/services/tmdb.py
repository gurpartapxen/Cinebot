import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import current_app
from datetime import datetime, timedelta

GENRE_MAP = {
    'action':      28,
    'adventure':   12,
    'animation':   16,
    'comedy':      35,
    'crime':       80,
    'documentary': 99,
    'drama':       18,
    'fantasy':     14,
    'horror':      27,
    'mystery':     9648,
    'romance':     10749,
    'sci-fi':      878,
    'thriller':    53,
    'western':     37,
}

MOOD_TO_GENRE = {
    'happy':       ['comedy', 'animation'],
    'sad':         ['drama', 'romance'],
    'excited':     ['action', 'adventure'],
    'scared':      ['horror', 'thriller'],
    'romantic':    ['romance', 'drama'],
    'curious':     ['documentary', 'mystery'],
    'adventurous': ['adventure', 'action'],
    'relaxed':     ['animation', 'comedy'],
    'bored':       ['action', 'sci-fi'],
}

HEADERS = {
    'User-Agent':      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Accept':          'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection':      'keep-alive',
    'Referer':         'https://www.themoviedb.org/',
}


def _make_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    retry = Retry(total=3, backoff_factor=1,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET"])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://',  adapter)
    return session


class TMDBService:
    def __init__(self):
        self.api_key  = current_app.config['TMDB_API_KEY']
        self.base_url = current_app.config['TMDB_BASE_URL']
        self.img_base = current_app.config['TMDB_IMAGE_BASE']
        self.session  = _make_session()

    def _parse(self, results):
        movies = []
        for r in results:
            if not r.get('id'):
                continue
            poster   = f"{self.img_base}{r['poster_path']}"                    if r.get('poster_path')   else None
            backdrop = f"https://image.tmdb.org/t/p/w1280{r['backdrop_path']}" if r.get('backdrop_path') else None
            movies.append({
                'id':           r.get('id'),
                'tmdb_id':      r.get('id'),
                'title':        r.get('title') or r.get('name', 'Unknown'),
                'year':         (r.get('release_date') or r.get('first_air_date', ''))[:4],
                'release_date': r.get('release_date', ''),
                'rating':       round(r.get('vote_average', 0), 1),
                'votes':        r.get('vote_count', 0),
                'poster':       poster,
                'backdrop':     backdrop,
                'overview':     r.get('overview', ''),
                'genre_ids':    r.get('genre_ids', []),
                'popularity':   r.get('popularity', 0),
            })
        return movies

    def _get(self, endpoint, params=None):
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        try:
            res = self.session.get(
                f"{self.base_url}{endpoint}",
                params=params, timeout=15
            )
            if res.status_code == 200:
                return res.json()
            return {}
        except Exception as e:
            print(f"TMDB error {endpoint}: {e}")
            try:
                self.session = _make_session()
                res = self.session.get(
                    f"{self.base_url}{endpoint}",
                    params=params, timeout=15
                )
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass
            return {}

    def _get_multi_page(self, endpoint, params=None, target=60):
        """Fetch multiple pages to get up to `target` results."""
        if params is None:
            params = {}
        all_results = []
        page = 1
        while len(all_results) < target:
            p = {**params, 'page': page}
            data = self._get(endpoint, p)
            results = data.get('results', [])
            if not results:
                break
            all_results.extend(results)
            total_pages = data.get('total_pages', 1)
            if page >= total_pages or page >= 4:
                break
            page += 1
        return all_results[:target]

    def get_popular(self, limit=60):
        results = self._get_multi_page('/movie/popular', target=limit)
        return self._parse(results)

    def get_top_rated(self, limit=60):
        results = self._get_multi_page('/movie/top_rated', target=limit)
        return self._parse(results)

    def get_trending(self, limit=60):
        results = self._get_multi_page('/trending/movie/week', target=limit)
        return self._parse(results)

    def get_now_playing(self, limit=40):
        today     = datetime.now().strftime('%Y-%m-%d')
        month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        results   = self._get_multi_page('/discover/movie', {
            'primary_release_date.gte': month_ago,
            'primary_release_date.lte': today,
            'sort_by':                  'popularity.desc',
            'with_release_type':        '3|2',
        }, target=limit)
        if not results:
            results = self._get_multi_page('/movie/now_playing', target=limit)
        return self._parse(results)

    def get_upcoming(self, limit=40):
        today      = datetime.now().strftime('%Y-%m-%d')
        two_months = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
        results    = self._get_multi_page('/discover/movie', {
            'primary_release_date.gte': today,
            'primary_release_date.lte': two_months,
            'sort_by':                  'popularity.desc',
            'with_release_type':        '3|2',
        }, target=limit)
        if not results:
            results = self._get_multi_page('/movie/upcoming', target=limit)
        return self._parse(results)

    def get_by_genre(self, genre_id, limit=60):
        results = self._get_multi_page('/discover/movie', {
            'with_genres': genre_id,
            'sort_by':     'popularity.desc',
        }, target=limit)
        return self._parse(results)

    def search_movies(self, query, limit=20):
        results = self._get_multi_page('/search/multi', {'query': query}, target=limit)
        return self._parse(results)

    def search_tv(self, query):
        data = self._get('/search/tv', {'query': query, 'page': 1})
        return self._parse(data.get('results', [])[:8])

    def get_movie_detail(self, movie_id):
        data = self._get(f'/movie/{movie_id}',
                         {'append_to_response': 'credits,videos,similar'})
        if not data or not data.get('id'):
            return None

        poster   = f"{self.img_base}{data['poster_path']}"                    if data.get('poster_path')   else None
        backdrop = f"https://image.tmdb.org/t/p/w1280{data['backdrop_path']}" if data.get('backdrop_path') else None

        trailer_key = None
        for v in data.get('videos', {}).get('results', []):
            if v.get('site') == 'YouTube' and v.get('type') == 'Trailer':
                if v.get('official') and not trailer_key:
                    trailer_key = v.get('key')
                elif not trailer_key:
                    trailer_key = v.get('key')

        cast = []
        for c in data.get('credits', {}).get('cast', [])[:10]:
            photo = f"{self.img_base}{c['profile_path']}" if c.get('profile_path') else None
            cast.append({'name': c.get('name',''), 'character': c.get('character',''), 'photo': photo})

        director = next((c.get('name') for c in data.get('credits', {}).get('crew', [])
                         if c.get('job') == 'Director'), None)

        similar = self._parse(data.get('similar', {}).get('results', [])[:10])

        return {
            'id':           data.get('id'),
            'title':        data.get('title', 'Unknown'),
            'year':         data.get('release_date', '')[:4],
            'release_date': data.get('release_date', ''),
            'rating':       round(data.get('vote_average', 0), 1),
            'votes':        data.get('vote_count', 0),
            'runtime':      data.get('runtime'),
            'overview':     data.get('overview', ''),
            'tagline':      data.get('tagline', ''),
            'poster':       poster,
            'backdrop':     backdrop,
            'genres':       [g['name'] for g in data.get('genres', [])],
            'trailer_key':  trailer_key,
            'cast':         cast,
            'director':     director,
            'similar':      similar,
            'status':       data.get('status', ''),
            'budget':       data.get('budget', 0),
            'revenue':      data.get('revenue', 0),
            'language':     data.get('original_language', '').upper(),
        }