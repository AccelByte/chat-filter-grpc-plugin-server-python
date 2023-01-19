# Copyright (c) 2023 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

from uuid import uuid4
from typing import Collection, Dict, List, Optional

import spacy
from profanity_filter import ProfanityFilter

from app.proto.filterService_pb2 import (
    ChatMessage,
    HealthCheckResponse,
    MessageBatchResult,
    MessageResult,
    DESCRIPTOR,
)
from app.proto.filterService_pb2_grpc import FilterServiceServicer


class AsyncFilterService(FilterServiceServicer):
    full_name: str = DESCRIPTOR.services_by_name["FilterService"].full_name

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        extra_profane_word_dictionaries: Optional[
            Dict[Optional[str], Collection[str]]
        ] = None,
    ) -> None:
        languages = languages if languages else ["en"]
        for language in languages:
            spacy.load(language)

        self.filter = ProfanityFilter()
        self.filter.extra_profane_word_dictionaries = extra_profane_word_dictionaries

    async def Check(self, request, context):
        return HealthCheckResponse(status=HealthCheckResponse.ServingStatus.SERVING)

    async def FilterBulk(self, request, context):
        data = [self.censor_chat_message(message) for message in request.messages]
        return MessageBatchResult(data=data)

    def censor_chat_message(self, chat_message: ChatMessage) -> MessageResult:
        action: MessageResult.Action = MessageResult.Action.PASS
        classification: List[MessageResult.Classification] = []
        censored_words: List[str] = []
        message: str = chat_message.message
        reference_id: str = uuid4().hex

        censored_message = message

        if self.filter.is_profane(message):
            censored_message = self.filter.censor(message)

            # action
            action = MessageResult.Action.CENSORED

            # classification
            classification.append(MessageResult.Classification.OTHER)

            # censored_words
            msgs = message.split()
            cmsgs = censored_message.split()
            if len(msgs) == len(cmsgs):
                for i in range(len(msgs)):
                    if msgs[i] != cmsgs[i]:
                        censored_words.append(msgs[i])

        return MessageResult(
            id=chat_message.id,
            timestamp=chat_message.timestamp,
            action=action,
            classification=classification,
            cencoredWords=censored_words,
            message=censored_message,
            referenceId=reference_id,
        )
