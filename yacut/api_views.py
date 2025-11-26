import re
from http import HTTPStatus

from flask import jsonify, request

from . import app, db
from .error_handlers import InvalidAPIUsage
from .models import URLMap
from .views import get_unique_short_id


def is_valid_short_id(custom_id):
    """Проверяет, что custom_id содержит только латинские буквы и цифры."""
    return bool(re.match(r'^[a-zA-Z0-9]+$', custom_id))


@app.route('/api/id/', methods=['POST'])
def add_link():
    if not request.data:
        raise InvalidAPIUsage('Отсутствует тело запроса')
    data = request.get_json()
    if not data:
        raise InvalidAPIUsage('Отсутствует тело запроса')
    if 'url' not in data:
        raise InvalidAPIUsage('"url" является обязательным полем!')

    custom_id = data.get('custom_id', '').strip()

    if not custom_id:
        short_id = get_unique_short_id()
    else:
        reserved_routes = ['files', 'upload_files', 'api']
        if custom_id in reserved_routes:
            raise InvalidAPIUsage(
                'Предложенный вариант короткой ссылки уже существует.'
            )
        if len(custom_id) > 16:
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки'
            )
        if not is_valid_short_id(custom_id):
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки'
            )
        if URLMap.query.filter_by(short=custom_id).first():
            raise InvalidAPIUsage(
                'Предложенный вариант короткой ссылки уже существует.'
            )
        short_id = custom_id

    url_map = URLMap(original=data['url'], short=short_id)
    db.session.add(url_map)
    db.session.commit()
    return jsonify(url_map.to_dict()), HTTPStatus.CREATED


@app.route('/api/id/<string:short_id>/', methods=['GET'])
def get_link(short_id):
    url_map = URLMap.query.filter_by(short=short_id).first()
    if not url_map:
        raise InvalidAPIUsage('Указанный id не найден', HTTPStatus.NOT_FOUND)
    return jsonify({'url': url_map.original}), HTTPStatus.OK