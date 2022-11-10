import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from requests.exceptions import RequestException

from exceptions import ServerError, StatusCodeError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('RACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

TOKENS = ('PRACTICUM_TOKEN', 'TELEGRAM_CHAT_ID', 'TELEGRAM_TOKEN')

BOT_ON = 'Бот запущен.'
TOKEN_ERROR = 'Отсутствуют переменные окружения: {}.'
TOKENS_NOT_FOUND = 'Отсутствуют переменные окружения.'
CONNECTION_ERROR = (
    'Произошел сбой при обращении к эндпоинту: {error}. '
    'Переданные параметры: {url}, {headers}, {params}.'
)
STATUS_CODE_ERROR = (
    'Запрос к эндпоинту вернул код {status_code}. '
    'Переданные параметры: {url}, {headers}, {params}.'
)
SERVER_ERROR = (
    'Сервер отказался обслуживать запрос. '
    'Причина под ключом {key}: {error}. '
    'Переданные параметры: {url}, {headers}, {params}.'
)
RESPONSE_IS_NOT_DICT = 'Ответ от API не типа dict, а {}.'
HOMEWORKS_NOT_IN_RESPONSE = 'Ключ "homeworks" отсутствует в словаре.'
HOMEWORKS_IS_NOT_LIST = 'Под ключом "homeworks" домашки не типа list, а {}.'
UNKNOWN_HOMEWORK_STATUS = 'Получен неизвестный статус домашки: {}.'
HOMEWORK_STATUS_CHANGED = 'Изменился статус проверки работы "{}". {}'
BASIC_ERROR = 'Сбой в работе программы. {}.'
SEND_MESSAGE_ERROR = 'Не удалось отправить сообщение о сбое "{}". Ошибка: {}.'
MESSAGE_IS_SENT = 'Было отправлено сообщение: "{}".'


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.info(MESSAGE_IS_SENT.format(message))


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса Практикум Домашка."""
    parameters = dict(
        params={'from_date': current_timestamp},
        url=ENDPOINT,
        headers=HEADERS,
    )
    try:
        response = requests.get(**parameters)
    except RequestException as error:
        raise ConnectionError(CONNECTION_ERROR.format(
            error=error,
            **parameters
        ))
    response_json = response.json()
    for key in ('error', 'code'):
        if key in response_json:
            raise ServerError(SERVER_ERROR.format(
                key=key,
                error=response_json[key],
                **parameters
            ))
    if response.status_code != HTTPStatus.OK:
        raise StatusCodeError(STATUS_CODE_ERROR.format(
            status_code=response.status_code,
            **parameters
        ))
    return response_json


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError(RESPONSE_IS_NOT_DICT.format(type(response)))
    if 'homeworks' not in response:
        raise KeyError(HOMEWORKS_NOT_IN_RESPONSE)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(HOMEWORKS_IS_NOT_LIST.format(type(homeworks)))
    return homeworks


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе ее статус."""
    name = homework['homework_name']
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(UNKNOWN_HOMEWORK_STATUS.format(status))
    return HOMEWORK_STATUS_CHANGED.format(
        name,
        HOMEWORK_VERDICTS[status]
    )


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens_not_found = [
        token for token in TOKENS if globals()[token] is None
    ]
    if tokens_not_found:
        logging.critical(TOKEN_ERROR.format(tokens_not_found))
        return False
    return [token for token in TOKENS]


def main():
    """Основная логика работы бота."""
    logging.debug(BOT_ON)
    if not check_tokens():
        raise ValueError(TOKENS_NOT_FOUND)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            current_timestamp = response.get('current_date', current_timestamp)
        except Exception as error:
            logging.exception(BASIC_ERROR.format(error))
            try:
                send_message(bot, message)
            except Exception as error:
                logging.exception(SEND_MESSAGE_ERROR.format(message, error))
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        format=(
            '%(asctime)s: '
            '[%(levelname)s] - '
            '%(funcName)s - '
            '%(lineno)d - '
            '%(message)s'
        ),
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(__file__ + '.log', mode='w'),
            logging.StreamHandler(stream=sys.stdout)
        ],
    )
    main()
