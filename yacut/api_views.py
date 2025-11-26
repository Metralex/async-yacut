from flask import jsonify, request
from http import HTTPStatus

from . import app, db
from .models import URLMap

from .error_handlers import InvalidAPIUsage


@app.route('/api/id/', methods=['POST'])
def add_link():
    data = request.get_json()
    if not data:
        raise InvalidAPIUsage('Отсутствует тело запроса')
    if 'url' not in data:
        raise InvalidAPIUsage('"url" является обязательным полем!')
    if 'custom_id' not in data:
        raise InvalidAPIUsage('"custom_id" является обязательным полем!')
    if len(data['custom_id']) > 16:
        raise InvalidAPIUsage('Указано недопустимое имя для короткой ссылки')
    if URLMap.query.filter_by(short=data['custom_id']).first():
        raise InvalidAPIUsage('Предложенный вариант короткой ссылки уже существует.')
    url_map = URLMap(original=data['url'], short=data['custom_id'])
    db.session.add(url_map)
    db.session.commit()
    return jsonify(url_map.to_dict()), HTTPStatus.CREATED



@app.route('/api/id/<string:short_id>/', methods=['GET'])
def get_link(short_id):
    url_map = URLMap.query.filter_by(short=short_id).first()
    if not url_map:
        raise InvalidAPIUsage('Указанный id не найден', HTTPStatus.NOT_FOUND)
    return jsonify(url_map.to_dict()), HTTPStatus.OK