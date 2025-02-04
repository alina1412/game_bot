from dataclasses import dataclass


@dataclass
class EventTypes:
    start_round = "start_round"
    choose_category = "choose_category"
    choose_price = "choose_price"
    ready = "ready"
    renew_players = "renew_players"
    show_stat = "show_stat"
    cat_in_bag = "cat_in_bag"
    cat_receiver = "cat_receiver"


@dataclass
class CatRoundParams:
    question_id: int | None = None
    text: str | None = ""
    from_id: int | None = None
    round_id: int | None = None
    limit: int | None = 10
