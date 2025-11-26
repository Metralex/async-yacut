from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, URLField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import MultipleFileField, FileAllowed, FileField, FileRequired


class URLMapForm(FlaskForm):
    original_link = URLField(
        "Длинная ссылка",
        validators=[
            DataRequired(message="Обязательное поле"),
            Length(1, 128, message="Слишком длинная ссылка"),
        ],
    )
    custom_id = StringField(
        "Короткая ссылка",
        validators=[Length(1, 16, message="Слишком длинная ссылка"), Optional()],
    )
    submit = SubmitField('Создать')

    images = MultipleFileField(
        validators=[
            FileAllowed(
                # Список разрешенных расширений для файлов.
                ['jpg', 'jpeg', 'png', 'gif', 'bmp'], 
                # Сообщение, в случае если расширение не совпадает.
                message=(
                    'Выберите файлы с расширением '
                    '.jpg, .jpeg, .png, .gif или .bmp'
                )
            )
        ]
    )


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
