# Copyright (c) 2023 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

import asyncio
import json
import logging

from argparse import ArgumentParser
from enum import IntFlag
from pathlib import Path
from typing import Optional

from environs import Env

from app.proto.filterService_pb2_grpc import add_FilterServiceServicer_to_server

from accelbyte_grpc_plugin import App, AppGRPCInterceptorOpt, AppGRPCServiceOpt
from accelbyte_grpc_plugin.interceptors.authorization import (
    AuthorizationServerInterceptor,
)
from accelbyte_grpc_plugin.interceptors.logging import (
    DebugLoggingServerInterceptor,
)
from accelbyte_grpc_plugin.interceptors.metrics import (
    MetricsServerInterceptor,
)
from accelbyte_grpc_plugin.opts.grpc_health_checking import GRPCHealthCheckingOpt
from accelbyte_grpc_plugin.opts.grpc_reflection import GRPCReflectionOpt
from accelbyte_grpc_plugin.opts.loki import LokiOpt
from accelbyte_grpc_plugin.opts.prometheus import PrometheusOpt
from accelbyte_grpc_plugin.opts.zipkin import ZipkinOpt

from app.services.filter_service import AsyncFilterService

DEFAULT_APP_PORT: int = 6565


class PermissionAction(IntFlag):
    CREATE = 0b0001
    READ = 0b0010
    UPDATE = 0b0100
    DELETE = 0b1000


async def main(port: int, profanities_file: Optional[str] = None, **kwargs) -> None:
    env = Env(
        eager=kwargs.get("env_eager", True),
        expand_vars=kwargs.get("env_expand_vars", False),
    )
    env.read_env(
        path=kwargs.get("env_path", None),
        recurse=kwargs.get("env_recurse", True),
        verbose=kwargs.get("env_verbose", False),
        override=kwargs.get("env_override", False),
    )

    opts = []
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    with env.prefixed("AB_"):
        base_url = env("BASE_URL", "https://demo.accelbyte.io")
        client_id = env("SECURITY_CLIENT_ID", None)
        client_secret = env("SECURITY_CLIENT_SECRET", None)
        namespace = env("NAMESPACE", "accelbyte")

    with env.prefixed(prefix="ENABLE_"):
        if env.bool("LOKI", True):
            opts.append(LokiOpt())
        if env.bool("PROMETHEUS", True):
            opts.append(PrometheusOpt())
        if env.bool("HEALTH_CHECKING", True):
            opts.append(GRPCHealthCheckingOpt())
        if env.bool("REFLECTION", True):
            opts.append(GRPCReflectionOpt())
        if env.bool("ZIPKIN", True):
            opts.append(ZipkinOpt())

    with env.prefixed(prefix="PLUGIN_GRPC_SERVER_AUTH_"):
        if env.bool("ENABLED", False):
            from accelbyte_py_sdk import AccelByteSDK
            from accelbyte_py_sdk.core import MyConfigRepository, InMemoryTokenRepository
            from accelbyte_py_sdk.token_validation.caching import CachingTokenValidator

            resource = env("RESOURCE", "ADMIN:NAMESPACE:{namespace}:CHAT:CONFIG")
            action = env.int("ACTION", int(PermissionAction.READ | PermissionAction.UPDATE))

            config = MyConfigRepository(
                base_url, client_id, client_secret, namespace=namespace
            )
            sdk = AccelByteSDK()
            sdk.initialize(options={"config": config, "token": InMemoryTokenRepository()})
            token_validator = CachingTokenValidator(sdk)
            auth_server_interceptor = AuthorizationServerInterceptor(
                resource=resource,
                action=action,
                namespace=namespace,
                token_validator=token_validator,
            )
            opts.append(AppGRPCInterceptorOpt(auth_server_interceptor))

    if env.bool("PLUGIN_GRPC_SERVER_LOGGING_ENABLED", False):
        opts.append(AppGRPCInterceptorOpt(DebugLoggingServerInterceptor(logger)))

    if env.bool("PLUGIN_GRPC_SERVER_METRICS_ENABLED", True):
        opts.append(AppGRPCInterceptorOpt(MetricsServerInterceptor()))

    # register Filter Service
    extra_profane_word_dictionaries = None
    if profanities_file is not None:
        profanities_file = Path(profanities_file)
        if profanities_file.exists():
            extra_profane_word_dictionaries = json.load(profanities_file.open())
    opts.append(
        AppGRPCServiceOpt(
            AsyncFilterService(
                extra_profane_word_dictionaries=extra_profane_word_dictionaries
            ),
            AsyncFilterService.full_name,
            add_FilterServiceServicer_to_server,
        )
    )

    await App(port, env, opts=opts).run()


def parse_args():
    parser = ArgumentParser()

    parser.add_argument(
        "-p",
        "--port",
        default=DEFAULT_APP_PORT,
        type=int,
        required=False,
        help="[P]ort",
    )

    parser.add_argument(
        "-f",
        "--profanities_file",
        default=None,
        type=str,
        required=False,
        help="Profanities [F]ile",
    )

    result = vars(parser.parse_args())

    return result


if __name__ == "__main__":
    asyncio.run(main(**parse_args()))
