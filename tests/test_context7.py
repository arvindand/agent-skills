"""Exercise the Context7 wrapper without credentials or network access."""

import contextlib
import importlib.util
import io
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/context7/scripts/context7.py'
spec = importlib.util.spec_from_file_location('context7_wrapper', SCRIPT)
context7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(context7)


class RequestTests(unittest.TestCase):
    def test_response_is_bounded_and_request_has_a_timeout(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'documentation'
        with patch.object(context7, 'urlopen', return_value=response) as request:
            self.assertEqual(context7.make_request('https://context7.com/example'), 'documentation')
        self.assertEqual(request.call_args.kwargs['timeout'], context7.REQUEST_TIMEOUT)
        response.__enter__.return_value.read.assert_called_once_with(context7.MAX_RESPONSE_BYTES + 1)

    def test_oversized_response_fails_with_actionable_message(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'x' * (context7.MAX_RESPONSE_BYTES + 1)
        with patch.object(context7, 'urlopen', return_value=response):
            self.assert_failure('narrow the query')

    def test_network_failures_exit_cleanly(self):
        cases = [
            (TimeoutError('request timed out'), 'timed out'),
            (URLError('offline'), 'offline'),
            (HTTPError('https://context7.com/example', 429, 'Too Many Requests', {}, None), 'Rate limited'),
            (HTTPError('https://context7.com/example', 302, 'Moved', {}, None), 'moved or been renamed'),
        ]
        for error, message in cases:
            with self.subTest(error=error), patch.object(context7, 'urlopen', side_effect=error):
                self.assert_failure(message)

    def assert_failure(self, message):
        output = io.StringIO()
        with contextlib.redirect_stderr(output), self.assertRaises(SystemExit) as failure:
            context7.make_request('https://context7.com/example')
        self.assertEqual(failure.exception.code, 1)
        self.assertIn(message, output.getvalue())


if __name__ == '__main__':
    unittest.main()
