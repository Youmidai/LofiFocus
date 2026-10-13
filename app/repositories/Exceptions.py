class RepositoryError(Exception):
    """Базовая ошибка слоя доступа к данным."""

class DuplicateError(RepositoryError):
    """Нарушение уникальности."""