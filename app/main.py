import logging
import os
import time
import json
from requests import get, Response, exceptions
from prometheus_client import start_http_server, Gauge

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class HttpMonitorExporter:
    def __init__(self) -> None:
        self.config = {}
        self.metrics = {}

    def create_gauge_for_metric(self, metric_name, metric_help):
        if self.metrics.get(metric_name) is None:
            self.metrics[metric_name] = Gauge(metric_name, metric_help, ['url'])

    def check_url(self, url) -> Response:
        try:
            response = get(url)
            logging.info(url + " -> " + response.text)
            return response
        except exceptions.ConnectionError:
            logging.error("Error Connecting")
        except exceptions.Timeout:
            logging.error("Timeout Error")
        except exceptions.RequestException:
            logging.error("Oops: Something Else")

    def set_value(self, url):
        response = self.check_url(url)
        if response is not None:
            for metric in self.config["metrics"]:
                if "up" in metric["name"]:
                    self.metrics[metric["name"]].labels(url).set(1 if (response.status_code == 200) else 0)
                if "response_ms" in metric["name"]:
                    self.metrics[metric["name"]].labels(url).set(response.elapsed.microseconds / 1000)

    def main(self):
        port = int(os.environ.get("EXPORTER_PORT", "9877"))
        start_http_server(port)
        with open("config.json", encoding='utf-8') as config_json:
            self.config = json.load(config_json)
            for metric in self.config["metrics"]:
                self.create_gauge_for_metric(metric["name"], metric["help"])
            while True:
                for url in self.config["urls"]:
                    self.set_value(url)
                time.sleep(int(self.config["sleep"]))


if __name__ == "__main__":
    c = HttpMonitorExporter()
    c.main()
