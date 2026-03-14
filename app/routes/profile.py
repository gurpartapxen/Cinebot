from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Watchlist, MovieRating, ChatSession

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def profile():
    watchlist   = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.added_at.desc()).all()
    ratings     = MovieRating.query.filter_by(user_id=current_user.id).order_by(MovieRating.rated_at.desc()).all()
    total_chats = ChatSession.query.filter_by(user_id=current_user.id, role='user').count()
    avg_rating  = round(sum(r.rating for r in ratings) / len(ratings), 1) if ratings else None
    return render_template('profile.html', watchlist=watchlist, ratings=ratings, total_chats=total_chats, avg_rating=avg_rating)

@profile_bp.route('/watchlist/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_watchlist(item_id):
    item = Watchlist.query.filter_by(id=item_id, user_id=current_user.id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('profile.profile'))