# python3 -m unittest -v tests.test_app

import random
from datetime import timedelta
from requests import Response

from unittest import TestCase, mock, main
from app.main import HttpMonitorExporter
from prometheus_client.core import Gauge


def mocked_requests_get(*args, **kwargs):
    class MockResponse(Response):
        text = ""

        def __init__(self):
            super().__init__()

            microseconds = random.uniform(0.1, 999.9) * 1000
            self.elapsed = timedelta(microseconds=microseconds)

            status_codes = [200, 503]
            status_code = status_codes[random.randint(0, 1)]
            self.status_code = status_code

            self.text = "OK" if status_code == 200 else "ERROR"

    return MockResponse()


class TestHttpMonitorExporter(TestCase):
    def setUp(self):
        self.app = HttpMonitorExporter()
        self.last_url = None

    def test_load_config(self):
        # Load config.json with parameters
        self.app.config = self.app.load_config("app/config.json")

        # Check parameters
        self.assertIsNotNone(self.app.config["sleep"])
        self.assertTrue(int(self.app.config["sleep"]))
        self.assertTrue(len(self.app.config["urls"]) > 0)
        self.assertTrue(len(self.app.config["metrics"]) > 0)

    def test_set_value(self):
        with mock.patch('requests.get') as mock_get:
            # Load config.json with parameters
            self.app.config = self.app.load_config("app/config.json")

            # Iterate the metrics from config and then create Prometheus Gauges for each of them
            for metric in self.app.config["metrics"]:
                self.app.create_gauge_for_metric(metric["name"], metric["help"])

            for url in self.app.config["urls"]:
                # Patch the GET request with a mock for testing purposes
                mock_get.return_value = mocked_requests_get()

                # Set the mocked url response to the metrics in the Gauges
                self.app.set_value(url)

                # Check if the response is 200 or 503
                self.assertIn(self.app.response.status_code, [200, 503])

                # This URL will be used in the next assert
                self.last_url = url

            for metric, gauge in self.app.metrics.items():
                # Validate the previous created gauges as InstanceOf Gauge
                self.assertIsInstance(gauge, Gauge)

                value = self.app.registry.get_sample_value(metric, {'url': self.last_url})
                if "up" in metric:
                    self.assertEqual(int(value), 1 if self.app.response.status_code == 200 else 0)
                if "response_ms" in metric:
                    self.assertEqual(value, self.app.response.elapsed.microseconds / 1000)


if __name__ == '__main__':
    main()
