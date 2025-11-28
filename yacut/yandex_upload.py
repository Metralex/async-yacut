import asyncio
import os
from http import HTTPStatus

import aiohttp
from flask import flash, render_template, request, session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from . import app, db
from .forms import FileUploadForm
from .models import URLMap
from .views import get_unique_short_id


@app.route('/files', methods=['GET', 'POST'])
def upload_files():
    """Страница для загрузки файлов на Яндекс Диск."""
    form = FileUploadForm()
    uploaded_files = session.get('uploaded_files', [])

    if request.method != 'POST':
        return render_template(
            'upload_files.html',
            form=form,
            uploaded_files=uploaded_files,
        )

    files = request.files.getlist('files')
    if not files or not any(file.filename for file in files):
        return render_template(
            'upload_files.html',
            form=form,
            uploaded_files=uploaded_files,
        )

    from flask import current_app

    with current_app.app_context():
        new_files = asyncio.run(
            upload_files_to_yandex_disk(files, request.host_url)
        )
    uploaded_files.extend(new_files)
    session['uploaded_files'] = uploaded_files

    if not new_files:
        return render_template(
            'upload_files.html',
            form=form,
            uploaded_files=uploaded_files,
        )

    flash(f'Успешно загружено файлов: {len(new_files)}', 'success')
    return render_template(
        'upload_files.html',
        form=form,
        uploaded_files=uploaded_files,
        new_files=new_files,
    )


# из-за flake8 C901 function is too complex разбил на части
async def _request_upload_href(session, base_url, headers, file_path):
    upload_url = f'{base_url}/v1/disk/resources/upload'
    try:
        async with session.get(
            upload_url,
            headers=headers,
            params={'path': file_path, 'overwrite': 'true'},
        ) as resp:
            if resp.status != HTTPStatus.OK:
                return None
            try:
                upload_data = await resp.json()
            except aiohttp.ContentTypeError:
                return None
            return upload_data.get('href')
    except (aiohttp.ClientError, aiohttp.ClientResponseError):
        return None


async def _upload_file(session, upload_href, file_content):
    if not upload_href:
        return False
    try:
        async with session.put(upload_href, data=file_content) as resp:
            return resp.status in (HTTPStatus.CREATED, HTTPStatus.ACCEPTED)
    except (aiohttp.ClientError, aiohttp.ClientResponseError):
        return False


async def _verify_upload(session, base_url, headers, file_path):
    download_url = f'{base_url}/v1/disk/resources/download'
    try:
        async with session.get(
            download_url, headers=headers, params={'path': file_path}
        ) as resp:
            if resp.status != HTTPStatus.OK:
                return False
            try:
                await resp.json()
            except aiohttp.ContentTypeError:
                return False
    except (aiohttp.ClientError, aiohttp.ClientResponseError):
        return False
    return True


def _build_short_link(file_path, base_host_url):
    try:
        url_map = URLMap.query.filter_by(original=file_path).first()
        if not url_map:
            short_id = get_unique_short_id()
            url_map = URLMap(original=file_path, short=short_id)
            db.session.add(url_map)
            db.session.commit()
        return f'{base_host_url.rstrip("/")}/{url_map.short}'
    except SQLAlchemyError:
        db.session.rollback()
        return None


async def upload_files_to_yandex_disk(files, base_host_url):
    """Асинхронная загрузка файлов на Яндекс Диск."""
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

            upload_href = await _request_upload_href(
                session, base_url, headers, file_path
            )
            if not upload_href:
                continue

            if not await _upload_file(session, upload_href, file_content):
                continue

            if not await _verify_upload(session, base_url, headers, file_path):
                continue

            short_link = _build_short_link(file_path, base_host_url)
            if not short_link:
                continue

            uploaded_files.append(
                {'filename': original_filename, 'short_link': short_link}
            )
    return uploaded_files
