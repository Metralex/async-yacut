import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
    # Загрузка конфигурации из переменных окружения
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///db.sqlite3')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Регистрация blueprints
    from yacut import views, api_views, errorhandlers
    app.register_blueprint(views.bp)
    app.register_blueprint(api_views.bp)
    app.register_blueprint(errorhandlers.bp)
    
    return app


app = create_app()

