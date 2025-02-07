import asyncio
import json
import random
import typing
from asyncio import Future
from urllib.parse import urlencode, urljoin

import httpx
from httpx import AsyncClient

from service.dataclasses import UserDto
from service.vk_api.dataclasses import (
    ChatInvite,
    Message,
    Update,
    UpdateEventMessage,
    UpdateMessage,
    UpdateObject,
)
from service.vk_api.poller import Poller
from service.vk_api.worker import Worker

# from app.base.base_accessor import BaseAccessor
if typing.TYPE_CHECKING:
    from fastapi import FastAPI


API_PATH = "https://api.vk.com/method/"
API_VERSION = "5.131"


class VkApiAccessor:
    def __init__(self, app: "FastAPI"):
        # super().__init__(app, *args, **kwargs)
        self.app = app

        self.session: AsyncClient | None = None
        self.key: str | None = None
        self.server: str | None = None
        self.poller: Poller | None = None
        self.worker: Worker | None = None
        self.ts: int | None = None
        self.token = app.config.bot.token
        self.group_id = app.config.bot.group_id

    @property
    def logger(self):
        return self.app.config.logger

    async def connect(self) -> None:
        self.session = httpx.AsyncClient()

        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)

        self.poller = Poller(self.app)
        self.logger.info("Vk Poller starts polling from api to queue")
        self.poller.start()

        self.worker = Worker(self.app)
        # self.logger.info("Worker starts getting from queue")
        # self.worker.start()

    async def disconnect(self) -> None:
        if self.session:
            await self.session.aclose()

        if self.poller:
            await self.poller.stop()
            self.logger.info("Vk Poller stopped")
        if self.worker:
            await self.worker.stop()
            self.logger.info("Worker stopped")

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        params.setdefault("v", API_VERSION)
        return f"{urljoin(host, method)}?{urlencode(params)}"

    async def _get_long_poll_service(self, type_access="groups") -> None:
        url = self._build_query(
            host=API_PATH,
            method=f"{type_access}.getLongPollServer",
            params={
                "group_id": self.group_id,
                "access_token": self.token,
            },
        )
        response = await self.session.get(url)
        if response.status_code == 200:
            json_body = json.loads(response.text)
            if "error" in json_body:
                self.logger.error(json_body["error"])
                return
            data = json_body["response"]
            self.key = data["key"]
            self.server = data["server"]
            self.ts = data["ts"]

    async def get_user_info(
        self, user_id, fields=("id", "first_name", "last_name")
    ) -> UserDto | None:
        """Api method users.get. Getting user information for user_id"""
        url = self._build_query(
            host=API_PATH,
            method="users.get",
            params={
                "group_id": self.group_id,
                "access_token": self.token,
                "user_ids": user_id,
                "fields": fields,
            },
        )
        response = await self.session.get(url)
        if response.status_code == 200:
            json_body = json.loads(response.text)
            if "error" in json_body:
                self.logger.error(json_body["error"])
                return None
            user_info: list[dict] = json_body["response"]
            user = user_info[0] if user_info else None
            if not user:
                return None
        return UserDto(
            vk_id=user["id"],
            first_name=user["first_name"],
            second_name=user["last_name"],
        )

    def get_members_user_only_list(self, data: dict) -> list[UserDto]:
        return [
            UserDto(
                vk_id=item["id"],
                first_name=item["first_name"],
                second_name=item["last_name"],
            )
            for item in data["profiles"]
        ]

    async def get_conversation_members(self, peer_id):
        """Метод получает список участников беседы."""
        url = self._build_query(
            host=API_PATH,
            method="messages.getConversationMembers",
            params={
                "group_id": self.app.config.bot.group_id,
                "access_token": self.app.config.bot.token,
                "peer_id": peer_id,
            },
        )
        response = await self.session.get(url)
        if response.status_code == 200:
            json_body = json.loads(response.text)
            if "error" in json_body:
                self.logger.error(json_body["error"])
                return None
            data: list[dict] = json_body["response"]

        return self.get_members_user_only_list(data)

    async def sent_answer_to_event(self, message: UpdateEventMessage):
        """Callback on button"""
        url = self._build_query(
            host=API_PATH,
            method="messages.sendMessageEventAnswer",
            params={
                "group_id": self.group_id,
                "access_token": self.token,
                "event_id": message.object.message.event_id,
                "user_id": message.object.message.from_id,
                "peer_id": message.object.message.peer_id,
            },
        )
        response = await self.session.get(url)
        if response.status_code == 200:
            json_body = json.loads(response.text)
            if "error" in json_body:
                self.logger.error(json_body["error"])

    def get_upd_obj_event_message(self, update) -> UpdateObject:
        return Update(
            type=update["type"],
            object=UpdateObject(
                message=UpdateEventMessage(
                    text="",
                    from_id=update["object"].get("user_id", None),
                    peer_id=update["object"].get("peer_id", None),
                    payload=update["object"].get("payload", None),
                    event_id=update["object"].get("event_id", None),
                )
            ),
        )

    def get_upd_obj_chat_invite(self, update) -> ChatInvite:
        member_id = (
            update["object"]["message"]["action"].get("member_id")
            if update["object"]["message"]["action"]["type"]
            == "chat_invite_user"
            else update["object"]["message"]["from_id"]
        )
        return ChatInvite(
            type="chat_invite_user",
            peer_id=update["object"]["message"].get("peer_id", None),
            member_id=member_id,
        )

    def get_upd_obj_update_message(self, update) -> UpdateObject:
        return Update(
            type=update["type"],
            object=UpdateObject(
                message=UpdateMessage(
                    id=update["object"]["message"]["id"],
                    from_id=update["object"]["message"]["from_id"],
                    text=update["object"]["message"]["text"],
                    peer_id=update["object"]["message"].get("peer_id", None),
                    payload=update["object"]["message"].get("payload", None),
                )
            ),
        )

    async def form_updates_lst(self, data: dict) -> list:
        """In chats"""
        updates = []
        for update in data.get("updates", []):
            cur_upd = None
            if update["type"] == "message_event":
                cur_upd = self.get_upd_obj_event_message(update)
            elif update["type"] == "message_new":
                action_type = (
                    update["object"]["message"]
                    .get("action", {})
                    .get("type", None)
                )
                if action_type in (
                    "chat_invite_user",
                    "chat_invite_user_by_link",
                ):
                    cur_upd = self.get_upd_obj_chat_invite(update)
                elif action_type == "chat_kick_user":
                    pass
                else:
                    cur_upd = self.get_upd_obj_update_message(update)
            if cur_upd:
                updates.append(cur_upd)
        return updates

    async def put_updates_to_queue(self, updates):
        self.append_task = asyncio.create_task(
            self.app.storage.que.send_to_que(bunch=updates)
        )
        self.append_task.add_done_callback(self._done_callback)

    async def poll(self):
        assert self.server
        url1 = self._build_query(
            host=self.server,
            method="",
            params={
                "act": "a_check",
                "key": self.key,
                "ts": self.ts,
                "wait": 30,
                "mode": 2,
                "version": 2,
            },
        )

        try:
            response = await self.session.get(url1, timeout=31)
            if response.status_code == 200:
                data = json.loads(response.text)
                self.logger.info(data)
                if "failed" in data:
                    self.logger.error("error: %s", str(data))
                    if data["failed"] == 1:
                        self.ts = data["ts"]
                    else:
                        await self._get_long_poll_service()
                    return
                self.ts = data["ts"]
                if data.get("updates", []):
                    updates = await self.form_updates_lst(data)
                    if updates:
                        await self.put_updates_to_queue(updates)
                        self.worker.start()  # receive_from_queue
                        await self.worker.stop()
                        # self.handle_task = asyncio.create_task(
                        #     self.app.storage.que.receive_from_queue()
                        # )
                        # self.handle_task.add_done_callback(self._done_callback)

        except httpx.ReadTimeout as e:
            self.logger.error("ReadTimeout %s", url1)
        except httpx.TimeoutException as e:
            self.logger.error("ReadTimeout %s", url1)
        except Exception as exc:
            self.logger.error("Exception", exc_info=exc)

    async def send_message(
        self,
        message: Message,
        keyboard: list | None = None,
        photo_id: str | None = None,
    ) -> None:
        url = self._build_query(
            API_PATH,
            "messages.send",
            params={
                "random_id": random.randint(1, 2**32),
                "peer_id": message.peer_id,
                "message": message.text,
                "access_token": self.app.config.bot.token,
                "attachment": photo_id,
                "keyboard": (
                    keyboard if keyboard else json.dumps({"buttons": []})
                ),  # , json.dumps() "one_time": True, "inline": False
            },
        )
        try:
            response = await self.session.get(url)
            if response.status_code == 200:
                data = json.loads(response.text)
                if "failed" in data or "error" in data:
                    self.logger.error("error: %s", str(data))
                self.logger.info(data)
        except httpx.TimeoutException as e:
            self.logger.error("TimeoutException")
        except httpx.ReadTimeout as e:
            self.logger.error("ReadTimeout")

    def _done_callback(self, result: Future) -> None:
        if result.exception():
            self.logger.exception(
                "task stopped with exception", exc_info=result.exception()
            )
