
import json
from pathlib import Path
import tempfile
import unittest

from unittest.mock import Mock, patch
import requests
from acquire import MetClient, iter_records, load_cache


# Mock responses exercise recovery behavior without accessing the API.
class AcquisitionTests(unittest.TestCase):

    def test_stops_after_consecutive_forbidden(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'cache.jsonl'
            client = Mock()
            response = Mock(status_code=403)

            client.get.side_effect = requests.HTTPError(response=response)
            self.assertEqual(list(iter_records(client, [1, 2, 3, 4, 5], path)), [])
            self.assertEqual(client.get.call_count, 3)


    def test_resume_does_not_refetch_cached_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'cache.jsonl'
            client = Mock()

            client.get.side_effect = [{'objectID': 1}, {'objectID': 2}]
            self.assertEqual(len(list(iter_records(client, [1, 2], path))), 2)
            self.assertEqual(len(list(iter_records(client, [1, 2], path))), 2)
            self.assertEqual(client.get.call_count, 2)
            self.assertEqual(len(path.read_text().splitlines()), 2)


    # Observe retry delays without waiting in the test runner.
    @patch('acquire.time.sleep')

    def test_429_retries_and_403_does_not(self, sleep):
        client = MetClient(interval=0)
        response = Mock(status_code=429, headers={'Retry-After': '3'})
        error = requests.HTTPError(response=response)
        good = Mock()
        good.json.return_value = {'departments': []}
        client.session.get = Mock(side_effect=[error, good])
        self.assertEqual(client.get('/departments'), {'departments': []})
        sleep.assert_any_call(3)

        response.status_code = 403
        client.session.get = Mock(side_effect=error)
        with self.assertRaises(requests.HTTPError):
            client.get('/departments')
        self.assertEqual(client.session.get.call_count, 1)


    def test_failed_id_can_be_retried_on_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'cache.jsonl'
            client = Mock()
            client.get.side_effect = requests.ConnectionError('offline')
            self.assertEqual(list(iter_records(client, [1], path)), [])

            client.get.side_effect = None
            client.get.return_value = {'objectID': 1}
            self.assertEqual(list(iter_records(client, [1], path)), [{'objectID': 1}])
            self.assertEqual(len(load_cache(path)), 1)


if __name__ == '__main__':
    unittest.main()
