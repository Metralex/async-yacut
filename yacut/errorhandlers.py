from flask import Blueprint, render_template

bp = Blueprint('errorhandlers', __name__)


@bp.app_errorhandler(404)
def page_not_found(error):
    """Обработчик ошибки 404."""
    return render_template('error.html', error_code=404, error_message='Страница не найдена'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    """Обработчик ошибки 500."""
    return render_template('error.html', error_code=500, error_message='Внутренняя ошибка сервера'), 500

