class GameFinishedError(Exception):
    def __init__(self, message="", errors=None):
        game_finished_message = (
            message
            + """
        game_finished_message
        """
        )
        super().__init__(game_finished_message)
        self.errors = errors
