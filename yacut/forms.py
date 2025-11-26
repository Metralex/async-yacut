import re

from flask_wtf import FlaskForm
from flask_wtf.file import (
    FileAllowed,
    FileField,
    FileRequired,
    MultipleFileField,
)
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional, ValidationError


def validate_custom_id(form, field):
    """Валидатор: custom_id только латинские буквы и цифры."""

    if field.data and not re.match(r'^[a-zA-Z0-9]+$', field.data):
        raise ValidationError('Недопустимые символы в короткой ссылке')


class URLMapForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=[
            DataRequired(message='Обязательное поле'),
            Length(1, 128, message='Слишком длинная ссылка'),
        ],
    )
    custom_id = StringField(
        'Короткая ссылка',
        validators=[
            Length(1, 16, message='Слишком длинная ссылка'),
            Optional(),
            validate_custom_id,
        ],
    )
    submit = SubmitField('Создать')

    images = MultipleFileField(
        validators=[
            FileAllowed(
                ['jpg', 'jpeg', 'png', 'gif', 'bmp'],
                message=(
                    'Выберите файлы с расширением '
                    '.jpg, .jpeg, .png, .gif или .bmp'
                ),
            )
        ]
    )


class FileUploadForm(FlaskForm):
    """Форма для загрузки файлов."""

    files = FileField(
        'Выберите файлы',
        validators=[FileRequired(message='Выберите хотя бы один файл')],
        render_kw={'multiple': True},
    )
    submit = SubmitField('Загрузить')
