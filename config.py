import os

class Config:
    SECRET_KEY                     = 'mysupersecretkey123'
    SQLALCHEMY_DATABASE_URI        = 'mysql+pymysql://chatbot_user:chatbot123@localhost/movie_chatbot_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY                 = os.environ.get('GEMINI_API_KEY')
    TMDB_API_KEY                   = os.environ.get('TMDB_API_KEY')
    TMDB_BASE_URL                  = 'https://api.themoviedb.org/3'
    TMDB_IMAGE_BASE                = 'https://image.tmdb.org/t/p/w500'