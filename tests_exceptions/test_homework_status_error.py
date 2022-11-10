# Запуск: python -m tests_exceptions.test_homework_status_error

from homework import main

if __name__ == '__main__':
    import logging
    import sys
    from unittest import TestCase, mock, main as uni_main

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

    JSON = {'homeworks': [{'homework_name': 'test', 'status': 'test'}]}

    class TestReq(TestCase):
        @mock.patch('requests.Response.json')
        def test_error(self, rq_get):
            rq_get.return_value = JSON
            main()
    uni_main()
