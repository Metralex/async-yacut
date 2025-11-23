import re
from flask import Blueprint, request, jsonify, url_for
from http import HTTPStatus

from yacut import db
from yacut.models import URLMap
from yacut.utils import get_unique_short_id

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/id/', methods=['POST'])
def create_id():
    """Создание новой короткой ссылки через API."""
    if not request.is_json:
        return jsonify({'message': 'Отсутствует тело запроса'}), HTTPStatus.BAD_REQUEST
    
    try:
        data = request.get_json(force=True)
    except Exception:
        data = None
    
    if not data:
        return jsonify({'message': 'Отсутствует тело запроса'}), HTTPStatus.BAD_REQUEST
    
    # Проверка обязательного поля url
    if 'url' not in data:
        return jsonify({'message': '"url" является обязательным полем!'}), HTTPStatus.BAD_REQUEST
    
    original_url = data.get('url')
    custom_id = data.get('custom_id', '').strip()
    
    # Валидация custom_id
    if custom_id:
        # Проверка длины
        if len(custom_id) > 16:
            return jsonify({'message': 'Указано недопустимое имя для короткой ссылки'}), HTTPStatus.BAD_REQUEST
        
        # Проверка на допустимые символы
        if not re.match(r'^[a-zA-Z0-9]+$', custom_id):
            return jsonify({'message': 'Указано недопустимое имя для короткой ссылки'}), HTTPStatus.BAD_REQUEST
        
        # Проверка на существование
        existing = URLMap.query.filter_by(short=custom_id).first()
        if existing:
            return jsonify({'message': 'Предложенный вариант короткой ссылки уже существует.'}), HTTPStatus.BAD_REQUEST
    else:
        # Генерация уникального идентификатора
        custom_id = get_unique_short_id()
    
    # Создание новой записи
    url_map = URLMap(original=original_url, short=custom_id)
    db.session.add(url_map)
    db.session.commit()
    
    short_link = url_for('views.redirect_view', short_id=custom_id, _external=True)
    return jsonify({
        'url': original_url,
        'short_link': short_link
    }), HTTPStatus.CREATED


@bp.route('/id/<short_id>/', methods=['GET'])
def get_url(short_id):
    """Получение оригинальной ссылки по короткому идентификатору."""
    url_map = URLMap.query.filter_by(short=short_id).first()
    if not url_map:
        return jsonify({'message': 'Указанный id не найден'}), HTTPStatus.NOT_FOUND
    
    return jsonify({'url': url_map.original}), HTTPStatus.OK

