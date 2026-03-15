from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.tmdb import TMDBService, GENRE_MAP
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

discover_bp = Blueprint('discover', __name__)

# ── Simple in-memory cache ──────────────────────────────────────────────────
_cache    = {}
CACHE_TTL = 300  # 5 minutes

def cache_get(key):
    if key in _cache:
        data, ts = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None

def cache_set(key, data):
    _cache[key] = (data, time.time())


# ── Pages ────────────────────────────────────────────────────────────────────

@discover_bp.route('/discover')
@login_required
def discover():
    return render_template('discover.html', genres=GENRE_MAP)


@discover_bp.route('/search')
@login_required
def search_page():
    query   = request.args.get('q', '').strip()
    results = []
    if query:
        try:
            tmdb    = TMDBService()
            results = tmdb.search_movies(query, limit=40)
        except Exception as e:
            print(f"Search error: {e}")
    return render_template('search.html', query=query, results=results)


@discover_bp.route('/movie/<int:movie_id>')
@login_required
def movie_detail(movie_id):
    tmdb  = TMDBService()
    movie = tmdb.get_movie_detail(movie_id)
    if not movie:
        return render_template('404.html'), 404
    return render_template('movie_detail.html', movie=movie)


# ── APIs ─────────────────────────────────────────────────────────────────────

@discover_bp.route('/api/discover')
@login_required
def api_discover():
    try:
        tmdb  = TMDBService()
        genre = request.args.get('genre', '').strip()
        tab   = request.args.get('tab', 'popular')
        limit = min(int(request.args.get('limit', 120)), 120)

        cache_key = f"discover:{tab}:{genre}:{limit}"
        cached    = cache_get(cache_key)
        if cached:
            return jsonify({'movies': cached})

        if genre and genre in GENRE_MAP:
            movies = tmdb.get_by_genre(GENRE_MAP[genre], limit=limit)
        elif tab == 'top_rated':
            movies = tmdb.get_top_rated(limit=limit)
        elif tab == 'upcoming':
            movies = tmdb.get_upcoming(limit=limit)
        elif tab == 'now_playing':
            movies = tmdb.get_now_playing(limit=limit)
        elif tab == 'trending':
            movies = tmdb.get_trending(limit=limit)
        else:
            movies = tmdb.get_popular(limit=limit)

        cache_set(cache_key, movies)
        return jsonify({'movies': movies})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'movies': []}), 500


@discover_bp.route('/api/search')
@login_required
def api_search():
    """Search API for live dropdown in navbar."""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': []})

    cache_key = f"search:{query.lower()}"
    cached    = cache_get(cache_key)
    if cached:
        return jsonify({'results': cached})

    try:
        tmdb    = TMDBService()
        results = tmdb.search_movies(query, limit=8)
        cache_set(cache_key, results)
        return jsonify({'results': results})
    except Exception as e:
        print(f"API search error: {e}")
        return jsonify({'results': [], 'error': str(e)})


@discover_bp.route('/api/auth-backdrops')
def auth_backdrops():
    cached = cache_get('auth_backdrops')
    if cached:
        data = {'backdrops': list(cached['backdrops'])}
        random.shuffle(data['backdrops'])
        return jsonify(data)

    ICONIC_MOVIES = [278, 238, 424, 155, 129, 27205, 157336, 497, 680, 13, 857, 637, 550, 120, 372058]

    try:
        import requests
        api_key   = '83fa498ec3c06e229e5332b90b7ca42a'
        base      = 'https://image.tmdb.org/t/p/w780'
        backdrops = []
        random.shuffle(ICONIC_MOVIES)

        def fetch_backdrop(mid):
            try:
                res  = requests.get(f'https://api.themoviedb.org/3/movie/{mid}',
                    params={'api_key': api_key}, headers={'User-Agent': 'Mozilla/5.0'}, timeout=6)
                data = res.json()
                path = data.get('backdrop_path') or data.get('poster_path')
                if path:
                    return {'url': f"{base}{path}", 'title': data.get('title', ''), 'year': data.get('release_date', '')[:4]}
            except Exception:
                pass
            return None

        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(fetch_backdrop, mid) for mid in ICONIC_MOVIES[:10]]
            for f in as_completed(futures):
                result = f.result()
                if result:
                    backdrops.append(result)

        random.shuffle(backdrops)
        result = {'backdrops': backdrops[:8]}
        cache_set('auth_backdrops', result)
        return jsonify(result)

    except Exception as e:
        print(f"Auth backdrops error: {e}")
        return jsonify({'backdrops': []})


@discover_bp.route('/api/director-spotlight')
@login_required
def director_spotlight():
    cached = cache_get('director_spotlight')
    if cached:
        directors = cached.get('directors', [])
        if directors:
            return jsonify(random.choice(directors))
        return jsonify({})

    DIRECTORS = [
        {'name': 'Christopher Nolan', 'person_id': 525, 'bio': 'Master of mind-bending narratives and practical effects.', 'movie_ids': [155, 27205, 157336, 49026]},
        {'name': 'Martin Scorsese',   'person_id': 1032, 'bio': 'The defining voice of American cinema for five decades.', 'movie_ids': [769, 493, 550988, 11917]},
        {'name': 'Quentin Tarantino', 'person_id': 138, 'bio': 'Iconic for non-linear storytelling and sharp dialogue.', 'movie_ids': [680, 193, 1058, 68721]},
        {'name': 'Denis Villeneuve',  'person_id': 137427, 'bio': 'Modern master of grand-scale science fiction.', 'movie_ids': [335984, 438631, 299536, 228150]},
    ]

    try:
        import requests
        api_key = '83fa498ec3c06e229e5332b90b7ca42a'
        headers = {'User-Agent': 'Mozilla/5.0'}

        def fetch_movie(mid):
            try:
                mr = requests.get(f'https://api.themoviedb.org/3/movie/{mid}', params={'api_key': api_key}, headers=headers, timeout=6)
                md = mr.json()
                return {'id': md.get('id'), 'title': md.get('title', ''), 'year': md.get('release_date', '')[:4],
                        'poster': f'https://image.tmdb.org/t/p/w300{md["poster_path"]}' if md.get('poster_path') else None}
            except Exception:
                return None

        def fetch_director(d):
            try:
                pr    = requests.get(f'https://api.themoviedb.org/3/person/{d["person_id"]}', params={'api_key': api_key}, headers=headers, timeout=6)
                pd    = pr.json()
                photo = f'https://image.tmdb.org/t/p/w300{pd["profile_path"]}' if pd.get('profile_path') else None
                with ThreadPoolExecutor(max_workers=4) as ex:
                    movies = [r for r in ex.map(fetch_movie, d['movie_ids']) if r]
                return {'name': d['name'], 'bio': d['bio'], 'photo': photo, 'movies': movies}
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=4) as ex:
            results = [r for r in ex.map(fetch_director, DIRECTORS) if r]

        cache_set('director_spotlight', {'directors': results})
        return jsonify(random.choice(results) if results else {})

    except Exception as e:
        print(f"Director spotlight error: {e}")
        return jsonify({})