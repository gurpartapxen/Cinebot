from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import User, Friendship, ActivityFeed, MovieReview

social_bp = Blueprint('social', __name__)


def log_activity(user_id, action, movie_title, movie_id, poster, details=''):
    """Helper to log an activity."""
    try:
        feed = ActivityFeed(
            user_id     = user_id,
            action      = action,
            movie_title = movie_title,
            movie_id    = movie_id,
            poster      = poster,
            details     = details
        )
        db.session.add(feed)
        db.session.commit()
    except Exception as e:
        print(f"Activity log error: {e}")

@social_bp.route('/activity')
@login_required
def activity():
    friend_ids = _get_friend_ids()

    # Always include self so your own activity shows
    all_ids = friend_ids + [current_user.id]

    feed = ActivityFeed.query\
        .filter(ActivityFeed.user_id.in_(all_ids))\
        .order_by(ActivityFeed.created_at.desc())\
        .limit(50).all()

    pending = Friendship.query.filter_by(
        addressee_id=current_user.id, status='pending'
    ).all()

    users = User.query.filter(User.id != current_user.id).all()

    return render_template('activity.html',
                           feed=feed,
                           pending=pending,
                           users=users,
                           friend_ids=friend_ids)


@social_bp.route('/api/friends/request', methods=['POST'])
@login_required
def send_request():
    data       = request.get_json()
    addressee  = User.query.get(data.get('user_id'))
    if not addressee or addressee.id == current_user.id:
        return jsonify({'error': 'Invalid user'}), 400
    existing = Friendship.query.filter_by(
        requester_id=current_user.id,
        addressee_id=addressee.id
    ).first()
    if existing:
        return jsonify({'status': 'already_sent'})
    f = Friendship(requester_id=current_user.id, addressee_id=addressee.id)
    db.session.add(f)
    db.session.commit()
    return jsonify({'status': 'sent'})


@social_bp.route('/api/friends/accept', methods=['POST'])
@login_required
def accept_request():
    data = request.get_json()
    f    = Friendship.query.filter_by(
        requester_id = data.get('user_id'),
        addressee_id = current_user.id,
        status       = 'pending'
    ).first()
    if not f:
        return jsonify({'error': 'Request not found'}), 404
    f.status = 'accepted'
    db.session.commit()
    return jsonify({'status': 'accepted'})


@social_bp.route('/api/friends/decline', methods=['POST'])
@login_required
def decline_request():
    data = request.get_json()
    f    = Friendship.query.filter_by(
        requester_id = data.get('user_id'),
        addressee_id = current_user.id,
        status       = 'pending'
    ).first()
    if f:
        db.session.delete(f)
        db.session.commit()
    return jsonify({'status': 'declined'})


@social_bp.route('/api/reviews/add', methods=['POST'])
@login_required
def add_review():
    data = request.get_json()
    if not data.get('review') or not data.get('tmdb_id'):
        return jsonify({'error': 'Missing fields'}), 400
    existing = MovieReview.query.filter_by(
        user_id=current_user.id, tmdb_id=data['tmdb_id']
    ).first()
    if existing:
        existing.review = data['review']
        existing.rating = data.get('rating')
    else:
        r = MovieReview(
            user_id = current_user.id,
            tmdb_id = data['tmdb_id'],
            title   = data.get('title', ''),
            poster  = data.get('poster', ''),
            rating  = data.get('rating'),
            review  = data['review']
        )
        db.session.add(r)
        # Log activity
        log_activity(
            current_user.id, 'reviewed',
            data.get('title', ''), data['tmdb_id'],
            data.get('poster', ''),
            f"rated {data.get('rating', '?')}/10"
        )
    db.session.commit()
    return jsonify({'status': 'saved'})


@social_bp.route('/api/reviews/<int:tmdb_id>')
@login_required
def get_reviews(tmdb_id):
    reviews = MovieReview.query\
        .filter_by(tmdb_id=tmdb_id)\
        .order_by(MovieReview.created_at.desc())\
        .limit(20).all()
    return jsonify([{
        'id':         r.id,
        'username':   r.user.username,
        'rating':     r.rating,
        'review':     r.review,
        'created_at': r.created_at.strftime('%d %b %Y'),
        'is_mine':    r.user_id == current_user.id,
    } for r in reviews])


@social_bp.route('/api/reviews/like/<int:review_id>', methods=['POST'])
@login_required
def like_review(review_id):
    r = MovieReview.query.get(review_id)
    if r:
        r.likes += 1
        db.session.commit()
    return jsonify({'likes': r.likes if r else 0})


def _get_friend_ids():
    accepted = Friendship.query.filter(
        db.or_(
            db.and_(Friendship.requester_id == current_user.id, Friendship.status == 'accepted'),
            db.and_(Friendship.addressee_id == current_user.id, Friendship.status == 'accepted')
        )
    ).all()
    ids = []
    for f in accepted:
        ids.append(f.addressee_id if f.requester_id == current_user.id else f.requester_id)
    return ids