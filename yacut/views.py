import os
from http import HTTPStatus
from random import randrange

import requests
from flask import abort, flash, redirect, render_template, session
from settings import ALLOWED_CHARS, SHORT_ID_LENGTH
from sqlalchemy import exists

from . import app, db
from .forms import URLMapForm
from .models import URLMap


def get_unique_short_id():
    """Генерирует уникальный короткий идентификатор"""
    while True:
        short_id = ''.join([ALLOWED_CHARS[randrange(
            len(ALLOWED_CHARS))] for _ in range(SHORT_ID_LENGTH)])
        if not db.session.query(
            exists().where(URLMap.short == short_id)
        ).scalar():
            return short_id


@app.route('/', methods=['GET', 'POST'])
def index_view():
    form = URLMapForm()
    link = None
    history = session.get('short_links', [])

    if not form.validate_on_submit():
        return render_template(
            'index.html', form=form, link=link, history=history
        )

    original_link = form.original_link.data
    custom_id = form.custom_id.data

    if custom_id:
        reserved_routes = ['files', 'upload_files', 'api']
        if custom_id in reserved_routes:
            flash('Предложенный вариант короткой ссылки уже существует.')
            return render_template(
                'index.html', form=form, link=None, history=history
            )
        if db.session.query(
            exists().where(URLMap.short == custom_id)
        ).scalar():
            flash('Предложенный вариант короткой ссылки уже существует.')
            return render_template(
                'index.html', form=form, link=None, history=history
            )
        short_id = custom_id
    else:
        short_id = get_unique_short_id()

    url_map = URLMap(original=original_link, short=short_id)
    db.session.add(url_map)
    db.session.commit()
    link = url_map
    flash('Ссылка успешно создана!', 'success')
    history.append({'original': original_link, 'short': link.short})
    session['short_links'] = history
    return render_template('index.html', form=form, link=link, history=history)


@app.route('/<short_link>')
def redirect_view(short_link):
    url_map = URLMap.query.filter_by(short=short_link).first()
    if not url_map:
        abort(HTTPStatus.NOT_FOUND)

    original = url_map.original
    if original.startswith('app:/') or original.startswith('/'):
        disk_token = os.getenv('DISK_TOKEN')
        base_url = 'https://cloud-api.yandex.net'
        download_url = f'{base_url}/v1/disk/resources/download'
        try:
            resp = requests.get(
                download_url,
                headers={'Authorization': f'OAuth {disk_token}'},
                params={'path': original},
            )
            resp.raise_for_status()
            href = resp.json()['href']
            return redirect(href)
        except (requests.RequestException, KeyError):
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

    return redirect(original)
