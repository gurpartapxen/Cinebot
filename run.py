import os
os.environ['GEMINI_API_KEY'] = 'AIzaSyAPfboW0SNCYNHqQGn5Ki9tDiIzIdYahDY'
os.environ['TMDB_API_KEY']   = '83fa498ec3c06e229e5332b90b7ca42a'

from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Auto creates any missing tables
        print('Ready!')
    app.run(debug=True, port=5000)