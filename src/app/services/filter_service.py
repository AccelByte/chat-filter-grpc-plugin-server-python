# Copyright (c) 2023 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

import json
from logging import Logger
from uuid import uuid4
from typing import Collection, Dict, List, Optional

import spacy
from google.protobuf.json_format import MessageToDict
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
        logger : Optional[Logger] = None,
    ) -> None:
        languages = languages if languages else ["en"]
        for language in languages:
            spacy.load(language)

        self.filter = ProfanityFilter()
        self.filter.extra_profane_word_dictionaries = extra_profane_word_dictionaries
        self.logger = logger

    async def Check(self, request, context):
        self.log_payload(f'{self.Check.__name__} request: %s', request)
        response = HealthCheckResponse(status=HealthCheckResponse.ServingStatus.SERVING)
        self.log_payload(f'{self.Check.__name__} response: %s', response)
        return response

    async def FilterBulk(self, request, context):
        self.log_payload(f'{self.FilterBulk.__name__} request: %s', request)
        data = [self.do_censor(message) for message in request.messages]
        response = MessageBatchResult(data=data)
        self.log_payload(f'{self.FilterBulk.__name__} response: %s', response)
        return response

    def do_censor(self, chat_message: ChatMessage) -> MessageResult:
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
            words = message.split()
            cwords = censored_message.split()
            if len(words) == len(cwords):
                censored_words = [words[i] for i in range(len(words)) if words[i] != cwords[i]]
        return MessageResult(
            id=chat_message.id,
            timestamp=chat_message.timestamp,
            action=action,
            classification=classification,
            cencoredWords=censored_words,
            message=censored_message,
            referenceId=reference_id,
        )
        
    def log_payload(self, format : str, payload):
        if not self.logger:
            return
        payload_dict = MessageToDict(payload, preserving_proto_field_name=True)
        payload_json = json.dumps(payload_dict)
        self.logger.info(format % payload_json)
