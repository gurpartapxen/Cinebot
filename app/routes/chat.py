from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import ChatSession, Watchlist, MovieRating

chat = Blueprint('chat', __name__)
_chatbots = {}


@chat.route('/')
@login_required
def index():
    sessions = db.session.query(
        ChatSession.session_id,
        ChatSession.title,
        db.func.max(ChatSession.created_at).label('last_at')
    ).filter_by(user_id=current_user.id)\
     .group_by(ChatSession.session_id, ChatSession.title)\
     .order_by(db.desc('last_at'))\
     .limit(15).all()

    history = ChatSession.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatSession.created_at.asc()).limit(40).all()

    return render_template('chat.html', history=history, sessions=sessions)


@chat.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    from app.services.chatbot import ChatbotService
    data    = request.get_json()
    message = data.get('message', '').strip()
    sess_id = data.get('session_id', str(current_user.id))

    if not message:
        return jsonify({'error': 'Empty message'}), 400

    try:
        if sess_id not in _chatbots:
            _chatbots[sess_id] = ChatbotService(session_id=sess_id)
        bot    = _chatbots[sess_id]
        result = bot.respond(message)

        existing = ChatSession.query.filter_by(
            user_id=current_user.id, session_id=sess_id
        ).first()
        title = existing.title if existing else message[:40]

        db.session.add(ChatSession(
            user_id=current_user.id, session_id=sess_id,
            title=title, message=message, role='user'
        ))
        db.session.add(ChatSession(
            user_id=current_user.id, session_id=sess_id,
            title=title, message=result['message'], role='assistant'
        ))
        db.session.commit()
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        msg = "Too many requests. Please wait a moment."
        if "quota" not in str(e).lower():
            msg = f"Error: {str(e)}"
        return jsonify({'error': msg}), 500


@chat.route('/api/bg-posters')
def bg_posters():
    from app.services.tmdb import TMDBService
    try:
        tmdb    = TMDBService()
        movies  = tmdb.get_popular(limit=20)
        movies2 = tmdb.get_by_genre(28, limit=10)
        movies3 = tmdb.get_by_genre(878, limit=10)
        all_m   = movies + movies2 + movies3
        posters = [m['poster'] for m in all_m if m.get('poster')][:18]
        return jsonify({'posters': posters})
    except Exception:
        return jsonify({'posters': []})


@chat.route('/api/watchlist/add', methods=['POST'])
@login_required
def add_watchlist():
    from app.routes.social import log_activity
    data = request.get_json()
    try:
        existing = Watchlist.query.filter_by(
            user_id=current_user.id, tmdb_id=data['tmdb_id']
        ).first()
        if existing:
            return jsonify({'status': 'already_added'})
        item = Watchlist(
            user_id=current_user.id,
            tmdb_id=data['tmdb_id'],
            title=data['title'],
            poster=data.get('poster', ''),
            year=data.get('year', ''),
            rating=data.get('rating', 0),
        )
        db.session.add(item)
        log_activity(current_user.id, 'watchlisted',
                     data['title'], data['tmdb_id'],
                     data.get('poster', ''))
        db.session.commit()
        return jsonify({'status': 'added'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat.route('/api/watchlist/remove', methods=['POST'])
@login_required
def remove_watchlist():
    data = request.get_json()
    try:
        item = Watchlist.query.filter_by(
            user_id=current_user.id, tmdb_id=data['tmdb_id']
        ).first()
        if item:
            db.session.delete(item)
            db.session.commit()
        return jsonify({'status': 'removed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat.route('/api/rate', methods=['POST'])
@login_required
def rate_movie():
    from app.routes.social import log_activity
    data = request.get_json()
    try:
        existing = MovieRating.query.filter_by(
            user_id=current_user.id, tmdb_id=data['tmdb_id']
        ).first()
        if existing:
            existing.rating  = data['rating']
            existing.review  = data.get('review', '')
        else:
            r = MovieRating(
                user_id=current_user.id,
                tmdb_id=data['tmdb_id'],
                title=data['title'],
                poster=data.get('poster', ''),
                year=data.get('year', ''),
                rating=data['rating'],
                review=data.get('review', '')
            )
            db.session.add(r)
            log_activity(current_user.id, 'rated',
                         data['title'], data['tmdb_id'],
                         data.get('poster', ''),
                         f"gave it {data['rating']}/10")
        db.session.commit()
        return jsonify({'status': 'rated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat.route('/api/session/<session_id>')
@login_required
def get_session(session_id):
    messages = ChatSession.query.filter_by(
        user_id=current_user.id, session_id=session_id
    ).order_by(ChatSession.created_at.asc()).all()
    return jsonify([{
        'role':       m.role,
        'message':    m.message,
        'created_at': m.created_at.isoformat()
    } for m in messages])