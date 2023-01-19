# Copyright (c) 2023 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

import grpc_reflection.v1alpha.reflection

from accelbyte_grpc_plugin import App, AppOptABC, AppOptOrder


class GRPCReflectionOpt(AppOptABC):
    def apply_order(self) -> AppOptOrder:
        return AppOptOrder.AFTER_ADD_GRPC_SERVICES

    def apply(self, app: App, *args, **kwargs) -> None:
        service_names = [
            grpc_reflection.v1alpha.reflection.SERVICE_NAME,
            *app.grpc_service_names,
        ]
        grpc_reflection.v1alpha.reflection.enable_server_reflection(
            service_names, app.grpc_server
        )
