# Copyright (c) 2023 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

import threading

from flask import Flask
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_client import start_http_server, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from accelbyte_grpc_plugin import App, AppOptABC, AppOptOrder


class PrometheusOpt(AppOptABC):
    def apply_order(self) -> AppOptOrder:
        return AppOptOrder.BEFORE_SET_OTEL_METER_PROVIDER

    def apply(self, app: App, *args, **kwargs) -> None:
        with app.env.prefixed(prefix="PROMETHEUS_"):
            addr = app.env("ADDR", "0.0.0.0")
            port = app.env.int("PORT", 8080)
            endpoint = app.env("ENDPOINT", "/metrics")
            prefix = app.env("PREFIX", app.service_name)
            flask_app = Flask(app.service_name)
            flask_app.wsgi_app = DispatcherMiddleware(
                flask_app.wsgi_app, mounts={endpoint: make_wsgi_app()}
            )
            threading.Thread(
                target=lambda: flask_app.run(
                    host=addr,
                    port=port,
                    debug=True,
                    use_reloader=False,
                )
            ).start()
            app.otel_metric_readers.append(PrometheusMetricReader(prefix=prefix))
