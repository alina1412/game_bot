import asyncio
import json
import typing
from dataclasses import asdict

import aio_pika
import pamqp
import pika
from aio_pika.abc import AbstractChannel, AbstractQueue
from app.base.base_accessor import BaseAccessor

from service.dataclasses import Update

if typing.TYPE_CHECKING:
    from app.web.app import Application


class QueueAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        self.app = app
        self.logger = self.app.logger
        self.credentials = None
        super().__init__(app, *args, **kwargs)

    async def connect(self, app: "Application"):
        self.username = self.app.config.rabbit.user
        self.password = str(self.app.config.rabbit.password)
        self.host = self.app.config.rabbit.host
        self.queue_title = self.app.config.rabbit.queue_title
        self.logger.info("QueueAccessor connect")
        self.credentials = pika.PlainCredentials(
            username=self.username, password=self.password
        )

        self.parameters = pika.ConnectionParameters(
            host=self.host,
            credentials=self.credentials,
            # virtual_host="amqp",
            port=5672,
        )

    async def disconnect(self, app: "Application"):
        self.logger.info("QueueAccessor disconnect")

    async def send_to_que(self, bunch: list[Update]) -> None:
        connection = pika.BlockingConnection(self.parameters)
        channel = connection.channel()
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
            self.logger.info("Sent %s", message)
        connection.close()

    async def process_message(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ) -> None:
        async with message.process(ignore_processed=True):
            encoded = message.body.decode("utf-8")
            message_dict = json.loads(encoded)
            await self.app.store.bots_manager.handle_updates(message_dict)

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
        loop = asyncio.get_event_loop()
        connection = await aio_pika.connect_robust(
            host=self.host,
            login=self.username,
            password=self.password,
            port=5672,
            loop=loop,
        )
        channel = await connection.channel()
        await channel.set_qos(1)
        try:
            await self.rabbitmq_fetching(channel)
        except pamqp.exceptions.AMQPFrameError:
            self.logger.error("closed connection AMQPFrameError")
        except KeyboardInterrupt:
            connection.close()
            self.logger.info("closed connection")
