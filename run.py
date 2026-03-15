import os
os.environ['GEMINI_API_KEY'] = 'AIzaSyAPfboW0SNCYNHqQGn5Ki9tDiIzIdYahDY'
os.environ['TMDB_API_KEY']   = '83fa498ec3c06e229e5332b90b7ca42a'

from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print('Ready!')
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))