# Copyright (c) 2023 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

import asyncio
from unittest import IsolatedAsyncioTestCase

import grpc.aio

from app.proto.filterService_pb2 import HealthCheckRequest, HealthCheckResponse
from app.proto.filterService_pb2 import ChatMessage, ChatMessageBulk
from app.proto.filterService_pb2 import MessageResult, MessageBatchResult
from app.proto.filterService_pb2_grpc import (
    FilterServiceStub,
    add_FilterServiceServicer_to_server,
)
from app.services.filter_service import AsyncFilterService

from accelbyte_grpc_plugin_tests import create_server


class AsyncFilterServiceTestCase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.service = AsyncFilterService(
            extra_profane_word_dictionaries={"en": {"dawg"}}
        )

    async def test_connection(self):
        addr = "localhost:50051"
        server = create_server(addr, [])
        add_FilterServiceServicer_to_server(self.service, server)

        await server.start()

        try:
            async with grpc.aio.insecure_channel(addr) as channel:
                # assert
                stub = FilterServiceStub(channel)
                request = HealthCheckRequest(service="test")

                # act
                response = await stub.Check(request)

                # assert
                self.assertIsNotNone(response)
                self.assertIsInstance(response, HealthCheckResponse)
        finally:
            await server.stop(grace=None)

    async def test_check_returns_health_check_response(self):
        # arrange
        request = HealthCheckRequest(service="test")

        # act
        response = await self.service.Check(request, None)

        # assert
        self.assertIsNotNone(response)
        self.assertIsInstance(response, HealthCheckResponse)

    async def test_filter_bulk_filters_profanities(self):
        # arrange
        messages = [
            ChatMessage(
                id="id",
                userId="userId",
                topicId="topicId",
                topicType=ChatMessage.TopicType.TOPIC_PERSONAL,
                timestamp=0,
                message="hey dawg",
            )
        ]
        request = ChatMessageBulk(messages=messages)

        # act
        response = await self.service.FilterBulk(request, None)

        # assert
        self.assertIsNotNone(response)
        self.assertIsInstance(response, MessageBatchResult)
        self.assertEqual(len(messages), len(response.data))
        self.assertEqual("hey ****", response.data[0].message)
