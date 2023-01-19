# Copyright (c) 2023 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

import logging_loki

from accelbyte_grpc_plugin import App, AppOptABC


class LokiOpt(AppOptABC):
    def __init__(
        self,
        url: str = "http://localhost:3100/loki/api/v1/push",
        username: str = "",
        password: str = "",
        version: str = "1",
    ) -> None:
        self.url = url
        self.username = username
        self.password = password
        self.version = version

    def apply(self, app: App, *args, **kwargs) -> None:
        with app.env.prefixed(prefix="LOKI_"):
            url = app.env("URL", self.url)
            username = app.env("USERNAME", self.username)
            password = app.env("PASSWORD", self.password)
            version = app.env("VERSION", self.version)
            auth = (username, password) if username else None
            hdlr = logging_loki.LokiHandler(url=url, auth=auth, version=version)
            app.logger.addHandler(hdlr=hdlr)
