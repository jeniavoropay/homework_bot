# Запуск: python -m tests_exceptions.test_connection_error

from homework import main

if __name__ == '__main__':
    import logging
    import sys
    from unittest import TestCase, mock, main as uni_main
    import requests

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

    ReqEx = requests.RequestException

    class TestReq(TestCase):
        @mock.patch('requests.get')
        def test_raised(self, rq_get):
            rq_get.side_effect = mock.Mock(
                side_effect=ReqEx('testing'))
            main()
    uni_main()
