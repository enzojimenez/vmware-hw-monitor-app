import os
import time
import json
import logging
import requests

from prometheus_client import start_http_server, Gauge, CollectorRegistry

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HttpMonitorExporter:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.config = {}
        self.metrics = {}
        self.response = None

    def load_config(self, config_file) -> json:
        with open(config_file, encoding='utf-8') as config_json:
            return json.load(config_json)

    def create_gauge_for_metric(self, metric_name, metric_help):
        if self.metrics.get(metric_name) is None:
            self.metrics[metric_name] = Gauge(metric_name, metric_help, ['url'], registry=self.registry)

    def check_url(self, url) -> requests.Response:
        try:
            self.response = requests.get(url)
            return self.response
        except requests.exceptions.ConnectionError:
            logging.error("Error Connecting")
        except requests.exceptions.Timeout:
            logging.error("Timeout Error")
        except requests.exceptions.RequestException:
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
        self.config = self.load_config("config.json")
        port = int(os.environ.get("EXPORTER_PORT", "9877"))
        start_http_server(port)
        for metric in self.config["metrics"]:
            self.create_gauge_for_metric(metric["name"], metric["help"])
        while True:
            for url in self.config["urls"]:
                self.set_value(url)
                logging.info(url + " -> "
                             + self.response.text + " -> "
                             + str(self.response.status_code) + " : "
                             + str(self.response.elapsed.microseconds))
            # Check the URLs every 10 seconds
            time.sleep(int(self.config["sleep"]))


if __name__ == "__main__":
    c = HttpMonitorExporter()
    c.main()
