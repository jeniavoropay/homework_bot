# Запуск: python -m tests_exceptions.test_status_code_error

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

    class TestReq(TestCase):
        @mock.patch('requests.get')
        def test_error(self, rq_get):
            resp = mock.Mock()
            resp.status_code = 333
            rq_get.return_value.status_code = resp.status_code
            main()
    uni_main()
