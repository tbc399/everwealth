import asyncio
import sys

from loguru import logger
from inspect import getfullargspec
from typing import Callable
from functools import update_wrapper
from collections import defaultdict

from .broker import SimpleBroker, MessageBroker
from .message import BaseMessage
from .subscriber import Subscriber


class Lucette:

    def __init__(self, broker=None):
        self.__subscriber_registry = defaultdict(list)
        self.__broker = broker or SimpleBroker()

    def add_subscriber(self, subscriber: Subscriber):
        for func, param_type, channel in subscriber.handlers:
            self.__subscriber_registry[channel].append((func, param_type))
            logger.info(f"Registered handler for message type {param_type.__name__} on channel {channel}")

    def subscribe(self, func: Callable):
        """
        todo: add check to have no more than one channel per message type
        """
        update_wrapper(self, func)
        arg_details = getfullargspec(func)
        if len(arg_details.args) != 1:
            raise AttributeError(
                'subscriber handler must have exactly one argument'
            )
        param_name = arg_details.args[0]
        param_type = arg_details.annotations.get(param_name, None)
        if param_type is None:
            raise AttributeError(
                'subscriber must either have a type hint on the '
                'message parameter or the channel must be given'
            )
        # todo: if type hint given, get the channel if there is one
        self.__subscriber_registry[param_type.channel].append((func, param_type))
        logger.info(f"Registering handler for message type {param_type} on channel {param_type.channel}")

    async def publish(self, msg: BaseMessage, channel=None):
        await self.__broker.publish_message(msg, channel)

    async def run(self):
        if self.__broker is None:
            raise AttributeError('No message broker has been registered')
        for channel in self.__subscriber_registry.keys():
            await self.__broker.subscribe_to_channel(channel)
        logger.info(f"Running with {self.__broker.__class__.__name__}")
        #TODO: Can this be async while?????
        while True:
            msg = await self.__broker.get_message()
            if msg is not None:
                logger.info(f"Received message {msg[1]} on channel {msg[0]}")
                handlers = self.__subscriber_registry[msg[0]]
                if handlers:
                    logger.debug(f"Found {len(handlers)} message handlers")
                    for func, msg_type in handlers:
                        await func(msg_type.parse_raw(msg[1]))
                else:
                    logger.warning("No message handlers found!")
            await asyncio.sleep(0.01)  # todo: add some advanced backoff logic when low traffic
