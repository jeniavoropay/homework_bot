class TokenError(Exception):
    """Отсутствует переменная окружения."""

    pass


class StatusCodeError(Exception):
    """Запрос к эндпоинту не вернул код 200."""

    pass


class ServerError(Exception):
    """Сервер отказался обслуживать запрос."""

    pass
