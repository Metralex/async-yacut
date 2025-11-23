import random
import string

from yacut import db
from yacut.models import URLMap


def get_unique_short_id(length=6):
    """
    Генерирует уникальный короткий идентификатор.
    
    Args:
        length: Длина идентификатора (по умолчанию 6)
    
    Returns:
        str: Уникальный короткий идентификатор
    """
    chars = string.ascii_letters + string.digits
    while True:
        short_id = ''.join(random.choices(chars, k=length))
        if not URLMap.query.filter_by(short=short_id).first():
            return short_id

