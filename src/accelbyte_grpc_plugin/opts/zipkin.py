# Copyright (c) 2023 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

import opentelemetry.trace
from opentelemetry.exporter.zipkin.proto.http import ZipkinExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from accelbyte_grpc_plugin import App, AppOptABC, AppOptOrder


class ZipkinOpt(AppOptABC):
    def apply_order(self) -> AppOptOrder:
        return AppOptOrder.AFTER_SET_OTEL_TRACER_PROVIDER

    def apply(self, app: App, *args, **kwargs) -> None:
        with app.env.prefixed(prefix="OTEL_EXPORTER_ZIPKIN_"):
            endpoint = app.env("ENDPOINT", "http://localhost:9411/api/v2/spans")
            span_exporter = ZipkinExporter(endpoint=endpoint)
            span_processor = BatchSpanProcessor(span_exporter=span_exporter)
            opentelemetry.trace.get_tracer_provider().add_span_processor(
                span_processor=span_processor
            )
