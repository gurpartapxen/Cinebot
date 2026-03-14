from app import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    bio           = db.Column(db.String(255), default='')

    watch_history = db.relationship('WatchHistory',  backref='user', lazy=True)
    preferences   = db.relationship('UserPreference', backref='user', lazy=True)
    chat_sessions = db.relationship('ChatSession',    backref='user', lazy=True)
    watchlist     = db.relationship('Watchlist',      backref='user', lazy=True)
    ratings       = db.relationship('MovieRating',    backref='user', lazy=True)
    reviews       = db.relationship('MovieReview',    backref='user', lazy=True)
    sent_requests     = db.relationship('Friendship', foreign_keys='Friendship.requester_id', backref='requester', lazy=True)
    received_requests = db.relationship('Friendship', foreign_keys='Friendship.addressee_id', backref='addressee', lazy=True)


class WatchHistory(db.Model):
    __tablename__ = 'watch_history'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tmdb_id    = db.Column(db.Integer)
    title      = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(20), default='movie')
    rating     = db.Column(db.Float)
    poster     = db.Column(db.String(500))
    watched_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    genre      = db.Column(db.String(50))
    mood       = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100))
    title      = db.Column(db.String(255), default='New Chat')
    message    = db.Column(db.Text, nullable=False)
    role       = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Watchlist(db.Model):
    __tablename__ = 'watchlist'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tmdb_id    = db.Column(db.Integer, nullable=False)
    title      = db.Column(db.String(255), nullable=False)
    poster     = db.Column(db.String(500))
    year       = db.Column(db.String(10))
    rating     = db.Column(db.Float)
    media_type = db.Column(db.String(20), default='movie')
    added_at   = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'tmdb_id', name='unique_user_movie'),)


class MovieRating(db.Model):
    __tablename__ = 'movie_ratings'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tmdb_id    = db.Column(db.Integer, nullable=False)
    title      = db.Column(db.String(255), nullable=False)
    poster     = db.Column(db.String(500))
    year       = db.Column(db.String(10))
    rating     = db.Column(db.Float, nullable=False)
    review     = db.Column(db.Text)
    rated_at   = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'tmdb_id', name='unique_user_rating'),)


class MovieReview(db.Model):
    __tablename__ = 'movie_reviews'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tmdb_id    = db.Column(db.Integer, nullable=False)
    title      = db.Column(db.String(255), nullable=False)
    poster     = db.Column(db.String(500))
    rating     = db.Column(db.Float)
    review     = db.Column(db.Text, nullable=False)
    likes      = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Friendship(db.Model):
    __tablename__ = 'friendships'
    id           = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    addressee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status       = db.Column(db.String(20), default='pending')  # pending, accepted
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('requester_id', 'addressee_id', name='unique_friendship'),)


class ActivityFeed(db.Model):
    __tablename__ = 'activity_feed'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action      = db.Column(db.String(50), nullable=False)  # rated, watchlisted, reviewed
    movie_title = db.Column(db.String(255))
    movie_id    = db.Column(db.Integer)
    poster      = db.Column(db.String(500))
    details     = db.Column(db.String(255))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user        = db.relationship('User', backref='activities', lazy=True,
                                  foreign_keys=[user_id])