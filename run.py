import os

# Auto-fix Railway MySQL URL format
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('mysql://'):
    os.environ['DATABASE_URL'] = db_url.replace('mysql://', 'mysql+pymysql://', 1)

from app import create_app, db
app = create_app()

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))