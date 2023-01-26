# Copyright (c) 2023 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

from grpc_health.v1 import health
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

from accelbyte_grpc_plugin import App, AppOptABC, AppOptOrder


class GRPCHealthCheckingOpt(AppOptABC):
    def apply_order(self) -> AppOptOrder:
        return AppOptOrder.BEFORE_ADD_GRPC_SERVICES

    def apply(self, app: App, *args, **kwargs) -> None:
        app.grpc_service_names.append(
            health_pb2.DESCRIPTOR.services_by_name["Health"].full_name
        )
        health_pb2_grpc.add_HealthServicer_to_server(
            health.aio.HealthServicer(), app.grpc_server
        )
