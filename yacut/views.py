import asyncio
import os
import string
from random import randrange

import aiohttp
import requests
from flask import abort, flash, redirect, render_template, request, session
from werkzeug.utils import secure_filename

from . import app, db
from .forms import FileUploadForm, URLMapForm
from .models import URLMap


def get_unique_short_id():
    """Генерирует уникальный короткий идентификатор"""
    chars = string.ascii_letters + string.digits
    while True:
        short_id = ''.join([chars[randrange(len(chars))] for _ in range(6)])
        if not URLMap.query.filter_by(short=short_id).first():
            return short_id


@app.route('/', methods=['GET', 'POST'])
def index_view():
    form = URLMapForm()
    link = None
    history = session.get('short_links', [])

    if form.validate_on_submit():
        original_link = form.original_link.data
        custom_id = form.custom_id.data

        if custom_id:
            reserved_routes = ['files', 'upload_files', 'api']
            if custom_id in reserved_routes:
                flash('Предложенный вариант короткой ссылки уже существует.')
                return render_template(
                    'index.html', form=form, link=None, history=history
                )
            if URLMap.query.filter_by(short=custom_id).first():
                flash('Предложенный вариант короткой ссылки уже существует.')
                return render_template(
                    'index.html', form=form, link=None, history=history
                )
            short_id = custom_id
        else:
            short_id = get_unique_short_id()

        url_map = URLMap(
            original=original_link,
            short=short_id
        )
        db.session.add(url_map)
        db.session.commit()
        link = url_map
        flash('Ссылка успешно создана!', 'success')
        history.append({
            'original': original_link,
            'short': link.short
        })
        session['short_links'] = history
    return render_template('index.html', form=form, link=link, history=history)


@app.route('/<short_link>')
def redirect_view(short_link):
    url_map = URLMap.query.filter_by(short=short_link).first()
    if not url_map:
        abort(404)

    original = url_map.original
    if original.startswith('app:/') or original.startswith('/'):
        disk_token = os.getenv('DISK_TOKEN')
        base_url = 'https://cloud-api.yandex.net'
        download_url = f'{base_url}/v1/disk/resources/download'
        resp = requests.get(
            download_url,
            headers={'Authorization': f'OAuth {disk_token}'},
            params={'path': original},
        )
        resp.raise_for_status()
        href = resp.json()['href']
        return redirect(href)

    return redirect(original)


@app.route('/files', methods=['GET', 'POST'])
def upload_files():
    """Страница для загрузки файлов на Яндекс Диск."""
    form = FileUploadForm()
    uploaded_files = session.get('uploaded_files', [])
    if request.method == 'POST':
        files = request.files.getlist('files')
        if files and any(f.filename for f in files):
            from flask import current_app
            with current_app.app_context():
                new_files = asyncio.run(upload_files_to_yandex_disk(
                    files, request.host_url
                ))
            uploaded_files.extend(new_files)
            session['uploaded_files'] = uploaded_files
            if new_files:
                flash(
                    f'Успешно загружено файлов: {len(new_files)}',
                    'success'
                )
                return render_template(
                    'upload_files.html',
                    form=form,
                    uploaded_files=uploaded_files,
                    new_files=new_files,
                )
    return render_template(
        'upload_files.html',
        form=form,
        uploaded_files=uploaded_files,
    )


async def upload_files_to_yandex_disk(files, base_host_url):
    """
    Асинхронная загрузка файлов на Яндекс Диск.
    """
    disk_token = os.getenv('DISK_TOKEN')
    if not disk_token:
        return []
    base_url = 'https://cloud-api.yandex.net'
    uploaded_files = []
    async with aiohttp.ClientSession() as session:
        headers = {'Authorization': f'OAuth {disk_token}'}
        for file in files:
            if not file or not file.filename:
                continue
            original_filename = file.filename
            filename = secure_filename(original_filename)
            file_path = 'app:/' + filename
            file_content = file.read()
            try:
                upload_url = f'{base_url}/v1/disk/resources/upload'
                async with session.get(
                    upload_url,
                    headers=headers,
                    params={'path': file_path, 'overwrite': 'true'}
                ) as resp:
                    if resp.status != 200:
                        continue
                    upload_data = await resp.json()
                    upload_href = upload_data.get('href')
                async with session.put(upload_href, data=file_content) as resp:
                    if resp.status not in (201, 202):
                        continue
                download_url = f'{base_url}/v1/disk/resources/download'
                async with session.get(
                    download_url,
                    headers=headers,
                    params={'path': file_path}
                ) as resp:
                    if resp.status != 200:
                        continue
                url_map = URLMap.query.filter_by(original=file_path).first()
                if not url_map:
                    short_id = get_unique_short_id()
                    url_map = URLMap(original=file_path, short=short_id)
                    db.session.add(url_map)
                    db.session.commit()
                short_link = f'{base_host_url.rstrip("/")}/{url_map.short}'
                uploaded_files.append(
                    {'filename': original_filename, 'short_link': short_link}
                )
            except Exception:
                continue
    return uploaded_files
