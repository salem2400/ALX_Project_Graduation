import logging
from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from extensions import db
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
migrate = Migrate()
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-default-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-default-jwt-secret-key')

# Error handling for database connection
try:
    db.init_app(app)
    migrate.init_app(app, db)
except Exception as e:
    logger.error(f"Error initializing database: {e}")

login_manager = LoginManager(app)
login_manager.login_view = 'routes.login'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Initialize routes
from routes import init_app
init_app(app)

@app.route('/test-static')
def test_static():
    return app.send_static_file('styles.css')

@app.route('/test-app')
def test_app():
    return "Flask Application is Working"

logger.info("Starting the Flask application...")
if __name__ == '__main__':
    logger.info("Running the application...")
    try:
        app.run(debug=True, port=5019)
    except Exception as e:
        logger.error(f"Error running the app: {e}")
