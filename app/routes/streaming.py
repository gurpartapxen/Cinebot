from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.services.tmdb import TMDBService

streaming_bp = Blueprint('streaming', __name__)

PLATFORMS = {
    'netflix':   {
        'id': 8, 'name': 'Netflix', 'color': '#E50914',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Netflix_2015_logo.svg/200px-Netflix_2015_logo.svg.png',
        'url': 'https://www.netflix.com/search?q='
    },
    'prime':     {
        'id': 9, 'name': 'Amazon Prime', 'color': '#00A8E1',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Amazon_Prime_Video_logo.svg/200px-Amazon_Prime_Video_logo.svg.png',
        'url': 'https://www.amazon.com/s?k='
    },
    'disney':    {
        'id': 337, 'name': 'Disney+', 'color': '#113CCF',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Disney%2B_logo.svg/200px-Disney%2B_logo.svg.png',
        'url': 'https://www.disneyplus.com/search/'
    },
    'apple':     {
        'id': 350, 'name': 'Apple TV+', 'color': '#000000',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/Apple_TV_Plus_Logo.svg/200px-Apple_TV_Plus_Logo.svg.png',
        'url': 'https://tv.apple.com/search?term='
    },
    'hbo':       {
        'id': 1899, 'name': 'Max', 'color': '#002BE7',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/HBO_Max_Logo.svg/200px-HBO_Max_Logo.svg.png',
        'url': 'https://www.max.com/search?q='
    },
    'paramount': {
        'id': 531, 'name': 'Paramount+', 'color': '#0064FF',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Paramount_Plus.svg/200px-Paramount_Plus.svg.png',
        'url': 'https://www.paramountplus.com/search/'
    },
    'hotstar':   {
        'id': 122, 'name': 'Hotstar', 'color': '#1F80E0',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Disney%2B_Hotstar_logo.svg/200px-Disney%2B_Hotstar_logo.svg.png',
        'url': 'https://www.hotstar.com/in/search?q='
    },
    'jiocinema': {
        'id': 220, 'name': 'JioCinema', 'color': '#8B00FF',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/JioCinema_logo.svg/200px-JioCinema_logo.svg.png',
        'url': 'https://www.jiocinema.com/search/'
    },
    'sonyliv':   {
        'id': 237, 'name': 'SonyLIV', 'color': '#FF3A3A',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/SonyLIV.svg/200px-SonyLIV.svg.png',
        'url': 'https://www.sonyliv.com/search?query='
    },
    'mubi':      {
        'id': 11, 'name': 'MUBI', 'color': '#1b1b1b',
        'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Mubi_logo_2017.svg/200px-Mubi_logo_2017.svg.png',
        'url': 'https://mubi.com/en/films?q='
    },
}


@streaming_bp.route('/streaming')
@login_required
def streaming():
    return render_template('streaming.html', platforms=PLATFORMS)


@streaming_bp.route('/api/streaming/movies/<platform>')
@login_required
def platform_movies(platform):
    if platform not in PLATFORMS:
        return jsonify({'error': 'Unknown platform', 'movies': []}), 404
    try:
        tmdb     = TMDBService()
        provider = PLATFORMS[platform]
        movies   = tmdb.get_movies_by_provider(provider['id'])
        return jsonify({'movies': movies, 'platform': provider})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'movies': []}), 500


@streaming_bp.route('/api/streaming/where/<int:movie_id>')
@login_required
def where_to_watch(movie_id):
    try:
        tmdb = TMDBService()
        data = tmdb.get_watch_providers(movie_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({'platforms': [], 'tmdb_link': ''}), 500