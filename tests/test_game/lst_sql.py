lst = [
    """insert into public.user 
            (first_name, second_name, vk_id)
            values ('first_name1', 'second_name1', 111)
        ;
        """,
    """insert into public.game
            (chat_id)
            values (5);
        ;
        """,
    # """insert into public.participant
    #         (game_id, user_id, score)
    #         values (1, 1, 0);
    #     ;
    #     """,
    """insert into quiz
            (question, answer, price, category)
            values ('Первая буква английского алфавита?', 'a', 100, 'common')
        ;
        """,
    """insert into quiz
            (question, answer, price, category)
            values ('Последняя буква английского алфавита?', 'z', 200, 'tv')
        ;
        """,
    """insert into quiz
            (question, answer, price, category)
            values ('photo-228193008_457239018', 'хогвартс', 200, 'tv')
        ;
        """,
    """insert into public.user 
            (first_name, second_name, vk_id)
            values ('first_name2', 'second_name2', 222)
        ;
        """,
    """insert into public.participant
            (game_id, user_id, score)
            values (1, 2, 0);
        ;
        """,
]
