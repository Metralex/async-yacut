from random import randrange
import string
from flask import abort, flash, redirect, render_template, url_for, request
import os
import aiohttp
from werkzeug.utils import secure_filename
from . import app, db
from .forms import URLMapForm
from .models import URLMap
import requests
from dotenv import load_dotenv
import asyncio
from .forms import FileUploadForm


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
    
    if form.validate_on_submit():
        original_link = form.original_link.data
        custom_id = form.custom_id.data
        
        # Если пользователь указал кастомный ID, проверяем его уникальность
        if custom_id:
            if URLMap.query.filter_by(short=custom_id).first():
                flash(f'Имя {custom_id} уже есть, попробуйте другое!')
                return render_template('index.html', form=form, link=None)
            short_id = custom_id
        else:
            # Генерируем случайный ID
            short_id = get_unique_short_id()
        
        # Создаем новую запись
        url_map = URLMap(
            original=original_link,
            short=short_id
        )
        db.session.add(url_map)
        db.session.commit()
        
        link = url_map
        flash('Ссылка успешно создана!', 'success')
    
    return render_template('index.html', form=form, link=link)


@app.route('/<short_link>')
def redirect_view(short_link):
    url_map = URLMap.query.filter_by(short=short_link).first()
    if url_map:
        return redirect(url_map.original)
    else:
        abort(404)


@app.route('/upload_files', methods=['GET', 'POST'])
def upload_files():
    """Страница для загрузки файлов на Яндекс Диск."""
    form = FileUploadForm()
    uploaded_files = []
    
    if request.method == 'POST':
        files = request.files.getlist('files')
        if files and any(f.filename for f in files):
            from flask import current_app
            with current_app.app_context():
                uploaded_files = asyncio.run(upload_files_to_yandex_disk(files, request.host_url))
    
    return render_template('upload_files.html', form=form, uploaded_files=uploaded_files)


async def upload_files_to_yandex_disk(files, base_host_url):
    """
    Асинхронная загрузка файлов на Яндекс Диск.
    
    Args:
        files: Список файлов для загрузки
        base_host_url: Базовый URL хоста для генерации коротких ссылок
    
    Returns:
        list: Список словарей с информацией о загруженных файлах
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
            file_path = f'/{filename}'
            file_content = file.read()
            
            try:
                # 1. Получение ссылки для загрузки
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
                
                # 2. Загрузка файла
                async with session.put(upload_href, data=file_content) as resp:
                    if resp.status not in (201, 202):
                        continue
                
                # 3. Получение ссылки для скачивания
                download_url = f'{base_url}/v1/disk/resources/download'
                async with session.get(
                    download_url,
                    headers=headers,
                    params={'path': file_path}
                ) as resp:
                    if resp.status != 200:
                        continue
                    download_data = await resp.json()
                    download_href = download_data.get('href')
                
                # 4. Создание короткой ссылки для скачивания
                short_id = get_unique_short_id()
                url_map = URLMap(original=download_href, short=short_id)
                db.session.add(url_map)
                db.session.commit()
                
                short_link = f'{base_host_url.rstrip("/")}/{short_id}'
                uploaded_files.append({
                    'filename': original_filename,
                    'short_link': short_link
                })
                
            except Exception as e:
                continue
    
    return uploaded_files