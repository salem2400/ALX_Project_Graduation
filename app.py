import logging
from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from extensions import db
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Ensure instance folder exists
    try:
        os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)
    except Exception as e:
        logger.error(f"Error creating instance directory: {e}")

    # Configuration of the database's absolute path
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'database.db')

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-default-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-default-jwt-secret-key')

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Initialize login manager
    login_manager = LoginManager(app)
    login_manager.login_view = 'routes.login'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # Initialize routes
    from routes import init_app
    init_app(app)

    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")

    return app

app = create_app()

@app.route('/test-static')
def test_static():
    return app.send_static_file('styles.css')

@app.route('/test-app')
def test_app():
    return "Flask Application is Working"

if __name__ == '__main__':
    logger.info("Starting the Flask application...")
    try:
        app.run(debug=True, port=5019)
    except Exception as e:
        logger.error(f"Error running the app: {e}")
