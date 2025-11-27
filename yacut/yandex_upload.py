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

            try:
                upload_url = f'{base_url}/v1/disk/resources/upload'
                async with session.get(
                    upload_url,
                    headers=headers,
                    params={'path': file_path, 'overwrite': 'true'},
                ) as resp:
                    if resp.status != HTTPStatus.OK:
                        continue
                    try:
                        upload_data = await resp.json()
                    except aiohttp.ContentTypeError:
                        continue
                    upload_href = upload_data.get('href')
                    if not upload_href:
                        continue
            except (aiohttp.ClientError, aiohttp.ClientResponseError):
                continue

            try:
                async with session.put(upload_href, data=file_content) as resp:
                    if resp.status not in [
                        HTTPStatus.CREATED,
                        HTTPStatus.ACCEPTED,
                    ]:
                        continue
            except (aiohttp.ClientError, aiohttp.ClientResponseError):
                continue

            try:
                download_url = f'{base_url}/v1/disk/resources/download'
                async with session.get(
                    download_url, headers=headers, params={'path': file_path}
                ) as resp:
                    if resp.status != HTTPStatus.OK:
                        continue
                    try:
                        await resp.json()
                    except aiohttp.ContentTypeError:
                        continue
            except (aiohttp.ClientError, aiohttp.ClientResponseError):
                continue

            try:
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
            except SQLAlchemyError:
                db.session.rollback()
                continue
    return uploaded_files
