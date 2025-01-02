from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from extensions import db

app = Flask(__name__)
migrate = Migrate()
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure random key in production

db.init_app(app)
migrate.init_app(app, db)
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

if __name__ == '__main__':
    app.run(debug=True, port=5019)
