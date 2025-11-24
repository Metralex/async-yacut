from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, URLField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import MultipleFileField, FileAllowed


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
