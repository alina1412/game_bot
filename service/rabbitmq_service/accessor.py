import asyncio
import json
import typing
from dataclasses import asdict

import aio_pika
import pamqp
import pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractQueue,
    AbstractRobustConnection,
)
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
        self.sync_connection: pika.BlockingConnection | None = None
        self.async_connection: AbstractRobustConnection | None = None
        self.async_channel: AbstractChannel | None = None

    @property
    def logger(self):
        return self.app.config.logger

    async def connect(self):
        if not self.sync_connection or self.sync_connection.is_closed:
            self.sync_connection = pika.BlockingConnection(self.parameters)
        if not self.async_connection or self.async_connection.is_closed:
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
        if self.async_channel:
            await self.async_channel.close()
        if self.sync_connection:
            self.sync_connection.close()
        if self.async_connection:
            await self.async_connection.close()
        self.logger.info("QueueAccessor disconnected")

    async def send_to_que(self, bunch: list[Update]) -> None:
        await self.connect()
        channel = self.sync_connection.channel()
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
        channel.close()

    async def process_message(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ) -> None:
        try:
            async with message.process(ignore_processed=True):
                encoded = message.body.decode("utf-8")
                message_dict = json.loads(encoded)
                await self.app.storage.bots_manager.handle_updates(message_dict)
                await message.ack()
                self.logger.info("consumed")
        except Exception as exc:
            self.logger.error(
                f"Error processing message {message}: ", exc_info=exc
            )
            await message.nack(requeue=False)  # drop message

    async def receive_from_queue(self) -> None:
        """Create connection to rabbitmq, start process of receiving data"""
        await self.connect()
        if not self.async_channel or self.async_channel.is_closed:
            self.async_channel = await self.async_connection.channel()
        await self.async_channel.set_qos(prefetch_count=1)
        queue: AbstractQueue = await self.async_channel.declare_queue(
            self.queue_title,
            durable=True,
            auto_delete=False,
        )
        try:
            await queue.consume(callback=self.process_message, no_ack=False)
        except pamqp.exceptions.AMQPFrameError:
            self.logger.error("closed connection AMQPFrameError")
        except KeyboardInterrupt:
            await self.async_connection.close()
            self.logger.info("QueueAccessor closed async_connection")
        # finally:
        #     await channel.close()
