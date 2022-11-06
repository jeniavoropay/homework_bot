import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import HomeworkStatusError

load_dotenv()

logging.basicConfig(
    format='%(asctime)s: %(levelname)s - %(message)s - %(lineno)d - %(name)s',
    level=logging.DEBUG,
    filename='homework_bot.log',
    filemode='w'
)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение было отправлено')
    except Exception as error:
        logger.error(f'Не удалось отправить сообщение: {error}')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса Практикум Домашка."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=params,
        )
    except Exception as error:
        logging.error(f'Произошла ошибка при обращении к эндпоинту: {error}')
    if response.status_code != HTTPStatus.OK:
        message = (f'Запрос к эндпоинту вернул код {response.status_code}')
        raise requests.exceptions.RequestException(message)
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        message = 'Ответ от API пришел не в формате словаря'
        logging.error(message)
        raise TypeError(message)
    if response.get('homeworks') is None:
        message = 'В ответе API нет ключа homeworks'
        logging.error(message)
        raise KeyError(message)
    if not isinstance(response['homeworks'], list):
        message = 'Домашние работы не в формате списка'
        logging.error(message)
        raise TypeError(message)
    if response['homeworks'] == []:
        logging.debug('Новые статусы домашек отсутствуют')
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе ее статус."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
    except KeyError as error:
        logger.error('Отсутствуют название или статус домашки')
        raise error
    if homework_status not in HOMEWORK_STATUSES:
        logger.error('Получен неизвестный статус домашки')
        raise HomeworkStatusError
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    env_vars = (PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN)
    for var in env_vars:
        if var is None:
            logger.critical(f'Отсутствует переменная окружения: {var}')
            return False
    return True


def main():
    """Основная логика работы бота."""
    logger.debug('Бот запущен')
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)
            current_timestamp = int(response['current_date'])
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            try:
                send_message(bot, message)
            except Exception as error:
                message = f'Не удалось отправить сообщение. Ошибка: {error}'
                logging.error(message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
