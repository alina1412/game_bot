from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass
class Message:
    user_id: int
    text: str
    peer_id: int


@dataclass_json
@dataclass
class UpdateMessage:
    from_id: int
    text: str
    id: int
    payload: str
    peer_id: int


@dataclass_json
@dataclass
class UpdateEventMessage:
    from_id: int
    text: str
    payload: dict
    peer_id: int
    event_id: str


@dataclass_json
@dataclass
class UpdateObject:
    message: UpdateMessage | UpdateEventMessage


@dataclass_json
@dataclass
class Update:
    type: str
    object: UpdateObject


@dataclass_json
@dataclass
class ChatInvite:
    type: str
    peer_id: int
    member_id: int


@dataclass
class BtnData:
    label: str
    payload: str


@dataclass
class Member:
    member_id: int
    first_name: str | None


@dataclass
class Members:
    count: int
    members: list[Member] | None
