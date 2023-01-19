# Copyright (c) 2023 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

import platform
from typing import Any, Awaitable, Callable, Dict, Optional

from grpc import HandlerCallDetails, RpcMethodHandler
from grpc.aio import ServerInterceptor
from prometheus_client import Counter


class MetricsServerInterceptor(ServerInterceptor):
    def __init__(
        self,
        meter_name: str = "com.accelbyte.app",
        meter_version: str = "1.0.0",
        labels: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not labels:
            labels = {"os": platform.system().lower()}

        self.meter_name = meter_name
        self.meter_version = meter_version
        self.labels = labels

        counter_name = "grpc_server_calls"
        counter_unit = "count"
        counter_description = "number of gRPC calls"

        self.counter = Counter(
            name=counter_name,
            documentation=counter_description,
            labelnames=labels.keys(),
            unit=counter_unit,
        )

    async def intercept_service(
        self,
        continuation: Callable[[HandlerCallDetails], Awaitable[RpcMethodHandler]],
        handler_call_details: HandlerCallDetails,
    ) -> RpcMethodHandler:
        self.counter.labels(**self.labels).inc(amount=1)
        return await continuation(handler_call_details)
