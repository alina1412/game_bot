import asyncio
import json
import typing
from dataclasses import asdict

import aio_pika
import pamqp
import pika
from aio_pika.abc import AbstractChannel, AbstractQueue

from service.vk_api.dataclasses import Update

# from app.base.base_accessor import BaseAccessor

# if typing.TYPE_CHECKING:
#     from app.web.app import Application


class QueueAccessor:
    def __init__(self, app):
        self.credentials = None
        self.app = app
        # super().__init__(app, *args, **kwargs)
        self.username = self.app.config.rabbit.user
        self.password = str(self.app.config.rabbit.password)
        self.host = self.app.config.rabbit.host
        self.queue_title = self.app.config.rabbit.queue_title
        # self.logger.info("QueueAccessor connect")
        self.credentials = pika.PlainCredentials(
            username=self.username, password=self.password
        )

        self.parameters = pika.ConnectionParameters(
            host=self.host,
            credentials=self.credentials,
            # virtual_host="amqp",
            port=5672,
        )
        self.sync_connection = None
        self.async_connection = None

    @property
    def logger(self):
        return self.app.config.logger

    async def connect(self):
        self.sync_connection = pika.BlockingConnection(self.parameters)
        loop = asyncio.get_event_loop()
        self.async_connection = await aio_pika.connect_robust(
            host=self.host,
            login=self.username,
            password=self.password,
            port=5672,
            loop=loop,
        )
        self.logger.info("QueueAccessor connect")

    async def disconnect(self):
        if self.sync_connection:
            self.sync_connection.close()
        if self.async_connection:
            await self.async_connection.close()
        self.logger.info("QueueAccessor disconnected")

    async def send_to_que(self, bunch: list[Update]) -> None:
        if not self.sync_connection:
            await self.connect()
        sync_connection = self.sync_connection
        channel = sync_connection.channel()
        channel.queue_declare(queue=self.queue_title, durable=True)

        for item in bunch:
            message = json.dumps(asdict(item))

            channel.basic_publish(
                exchange="",
                routing_key=self.queue_title,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                ),
            )
            self.logger.info("Sent to_que %s", message)

    async def process_message(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ) -> None:
        async with message.process(ignore_processed=True):
            encoded = message.body.decode("utf-8")
            message_dict = json.loads(encoded)
            await self.app.storage.bots_manager.handle_updates(message_dict)

            await message.ack()
            self.logger.info("consumed")

    async def rabbitmq_fetching(self, channel: AbstractChannel) -> None:
        """Consume messages from rabbitmq"""
        queue: AbstractQueue = await channel.declare_queue(
            self.queue_title,
            durable=True,
            auto_delete=False,
        )
        await queue.consume(callback=self.process_message, no_ack=False)

    async def receive_from_queue(self) -> None:
        """Create connection to rabbitmq, start process of receiving data"""
        if not self.async_connection:
            await self.connect()
        async_connection = self.async_connection
        channel = await async_connection.channel()
        await channel.set_qos(1)
        try:
            await self.rabbitmq_fetching(channel)
        except pamqp.exceptions.AMQPFrameError:
            self.logger.error("closed connection AMQPFrameError")
        except KeyboardInterrupt:
            await async_connection.close()
            self.logger.info("QueueAccessor closed async_connection")
