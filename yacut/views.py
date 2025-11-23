import asyncio
import aiohttp
import os
from flask import Blueprint, render_template, flash, request, url_for, redirect
from werkzeug.utils import secure_filename

from yacut import db
from yacut.forms import URLForm, FileUploadForm
from yacut.models import URLMap
from yacut.utils import get_unique_short_id

bp = Blueprint('views', __name__)


@bp.route('/', methods=['GET', 'POST'])
def index_view():
    """Главная страница для создания коротких ссылок."""
    form = URLForm()
    if form.validate_on_submit():
        original = form.original_link.data
        custom_id = form.custom_id.data.strip() if form.custom_id.data else None
        
        # Проверка на существование custom_id
        if custom_id:
            existing = URLMap.query.filter_by(short=custom_id).first()
            if existing:
                flash('Предложенный вариант короткой ссылки уже существует.', 'error')
                return render_template('index.html', form=form)
        else:
            custom_id = get_unique_short_id()
        
        # Создание новой записи
        url_map = URLMap(original=original, short=custom_id)
        db.session.add(url_map)
        db.session.commit()
        
        short_link = url_for('views.redirect_view', short_id=custom_id, _external=True)
        flash(f'Ваша новая ссылка готова: {short_link}', 'success')
        return render_template('index.html', form=form, short_link=short_link)
    
    return render_template('index.html', form=form)


@bp.route('/files', methods=['GET', 'POST'])
def files_view():
    """Страница для загрузки файлов на Яндекс Диск."""
    form = FileUploadForm()
    uploaded_files = []
    
    if request.method == 'POST':
        files = request.files.getlist('files')
        if files and any(f.filename for f in files):
            from flask import current_app
            with current_app.app_context():
                uploaded_files = asyncio.run(upload_files_to_yandex_disk(files, request.host_url))
    
    return render_template('files.html', form=form, uploaded_files=uploaded_files)


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


@bp.route('/<short_id>')
def redirect_view(short_id):
    """Редирект на оригинальную ссылку по короткому идентификатору."""
    url_map = URLMap.query.filter_by(short=short_id).first_or_404()
    return redirect(url_map.original)

