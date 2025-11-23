import re
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, URLField, SubmitField
from wtforms.validators import DataRequired, URL, ValidationError, Optional, Length


class URLForm(FlaskForm):
    """Форма для главной страницы."""
    original_link = URLField(
        'Длинная ссылка',
        validators=[DataRequired(message='Обязательное поле')]
    )
    custom_id = StringField(
        'Ваш вариант короткой ссылки',
        validators=[
            Optional(),
            Length(max=16, message='Максимальная длина 16 символов')
        ]
    )
    submit = SubmitField('Создать')

    def validate_custom_id(self, field):
        """Валидация пользовательского варианта короткой ссылки."""
        if field.data:
            # Проверка на допустимые символы: только латинские буквы и цифры
            if not re.match(r'^[a-zA-Z0-9]+$', field.data):
                raise ValidationError('Указано недопустимое имя для короткой ссылки')
            # Проверка на зарезервированные пути
            if field.data == 'files':
                raise ValidationError('Предложенный вариант короткой ссылки уже существует.')


class FileUploadForm(FlaskForm):
    """Форма для загрузки файлов."""
    files = FileField(
        'Выберите файлы',
        validators=[
            FileRequired(message='Выберите хотя бы один файл')
        ],
        render_kw={'multiple': True}
    )
    submit = SubmitField('Загрузить')

