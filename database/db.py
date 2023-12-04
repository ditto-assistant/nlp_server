import logging
import sqlite3
import json
import time
from contextlib import closing

# setup logging for this module
log = logging.getLogger("db")
log.setLevel(logging.DEBUG)


class DittoDB:
    """
    This class contains helper functions for operations around a user's database.
    """

    def __init__(self):
        self.SQL = sqlite3.connect("database/ditto.db")
        self.run_sql_file("database/create_tables.sql")
        with closing(self.SQL.cursor()) as c:
            version = c.execute(
                "SELECT id FROM migrations ORDER BY id desc LIMIT 1"
            ).fetchone()[0]
        log.info(f"Connected to ditto.db! version: {version}")

    def run_sql_file(self, file_path: str):
        """
        This function runs a sql file.
        param file_path: The path to the sql file.
        """
        with open(file_path, "r") as f:
            with closing(self.SQL.cursor()) as c:
                c.executescript(f.read())

    def get_prompt_response_count(self, user_id: str) -> int:
        """
        This function returns the number of prompts and responses in the user's database.
        param user_id: The user's id.
        return: The number of prompts and responses in the user's database.
        """
        try:
            cur = self.SQL.cursor()
            prompt_count = cur.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
            response_count = cur.execute("SELECT COUNT(*) FROM responses").fetchone()[0]
        except Exception as e:
            prompt_count = 0
            response_count = 0
        return int(prompt_count) + int(response_count)

    def get_create_user_id(self, email: str) -> int:
        """
        This function returns the user's id.
        If the user does not exist, it creates a new user and returns the generated id.
        param email: The user's email.
        return: The user's id.
        """
        with closing(self.SQL.cursor()) as c:
            user_id = c.execute(
                """
                SELECT id FROM users WHERE email = ?
                """,
                (email,),
            ).fetchone()
            if user_id is None:
                c.execute(
                    """
                    INSERT INTO users (email) VALUES (?)
                    """,
                    (email,),
                )
                self.SQL.commit()
                user_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
            else:
                user_id = user_id[0]
            return user_id

    def get_chat_latest(self, user_id: int, conv_id: int):
        """
        This function returns the latest chat for the user.
        """
        return self.get_chats(
            user_id,
            conv_id,
            0,
            1,
            False,
        )

    def get_conversations(self, user_id: int, offset: int, limit: int, is_asc: bool):
        order = "ASC" if is_asc else "DESC"
        log.info(f"Getting conversations for user: {user_id}")
        with closing(self.SQL.cursor()) as c:
            return c.execute(
                f"""
                    WITH RankedConversations AS (
                        SELECT
                            conv.created_at,
                            conv.updated_at,
                            conv.chat_count,
                            ROW_NUMBER() OVER (
                                ORDER BY
                                    conv.updated_at
                            ) AS conv_index,
                            conv.title
                        FROM
                            conversations conv
                        WHERE
                            conv.user_id = ?
                    )
                    SELECT
                        conv_index,
                        title,
                        chat_count,
                        created_at,
                        updated_at
                    FROM RankedConversations
                    ORDER BY updated_at {order}
                    LIMIT ? OFFSET ? 
                    """,
                (user_id, limit, offset),
            ).fetchall()

    def get_chats(
        self, user_id: int, conv_id: int, offset: int, limit: int, is_asc: bool
    ):
        order = "ASC" if is_asc else "DESC"
        log.info(f"Getting chats for user: {user_id} conv_id: {conv_id}")
        with closing(self.SQL.cursor()) as c:
            return c.execute(
                f"""
                    WITH RankedChats AS (
                        SELECT
                            c.id AS chat_id,
                            c.is_user,
                            c.msg,
                            c.timestamp,
                            ROW_NUMBER() OVER (
                                ORDER BY
                                    c.timestamp
                            ) AS chat_index
                        FROM
                            chats c
                            INNER JOIN conversations conv ON c.conv_id = conv.id
                        WHERE
                            conv.user_id = ?
                            AND conv.id = ?
                    )
                    SELECT
                        chat_index,
                        is_user,
                        msg,
                        timestamp
                    FROM RankedChats
                    ORDER BY timestamp {order}
                    LIMIT ? OFFSET ? 
                    """,
                (user_id, conv_id, limit, offset),
            ).fetchall()

    def get_conversation_history(self, user_id: str):
        def create_response_arrays(arr):
            response = dict()
            for ndx, x in enumerate(arr):
                response[str(ndx)] = [x[0], x[1]]
            return json.dumps(response)

        try:
            cur = self.SQL.cursor()
            return create_response_arrays(prompts), create_response_arrays(responses)
        except Exception as e:
            prompts = []
            responses = []
            return None

    def new_conversation(self, user_id: int) -> int:
        """
        This function creates a new conversation for the user.
        param user_id: The user's id.
        return: The conversation id.
        """
        log.info(f"Creating new conversation for user {user_id}")
        with closing(self.SQL.cursor()) as c:
            c.execute(
                """
                INSERT INTO conversations (user_id, created_at, viewed_at)
                VALUES (?, datetime('now'), datetime('now'))
                """,
                (user_id,),
            )
            self.SQL.commit()
            return c.execute("SELECT last_insert_rowid()").fetchone()[0]

    def save_prompt(self, user_id: int, conv_id: int, prompt: str):
        log.info(f"Saving prompt for user: {user_id} conv_id: {conv_id}")
        with closing(self.SQL.cursor()) as c:
            c.execute(
                add_chat_sql,
                (conv_id, True, prompt),
            )
            c.execute(
                bump_conv_sql,
                (conv_id,),
            )
            self.SQL.commit()

    def save_response(self, user_id: int, conv_id: int, response: str):
        log.info(f"Saving response for user: {user_id} conv_id: {conv_id}")
        with closing(self.SQL.cursor()) as c:
            c.execute(
                add_chat_sql,
                (conv_id, False, response),
            )
            c.execute(
                bump_conv_sql,
                (conv_id,),
            )
            self.SQL.commit()

    def get_latest_conv_chat_id(self, user_id: int, conv_idx: int) -> (int, int):
        log.debug(f"Getting raw_chat_id for user: {user_id} with conv_idx: {conv_idx}")
        conv_id = self.get_create_conv_id(user_id, conv_idx)
        log.debug(f"conv_id: {conv_id}")
        with closing(self.SQL.cursor()) as c:
            return (
                conv_id,
                c.execute(
                    """
                SELECT MAX(id) FROM chats WHERE conv_id = ?
                """,
                    (conv_id,),
                ).fetchone()[0],
            )

    def get_conv_id(self, user_id: int, conv_idx: int) -> int:
        log.debug(f"Getting raw_conv_id for user: {user_id} with conv_idx: {conv_idx}")
        with closing(self.SQL.cursor()) as c:
            return c.execute(
                """
                WITH RankedConversations AS (
                    SELECT
                        conv.id AS conv_id,
                        ROW_NUMBER() OVER (
                            ORDER BY conv.id ASC
                        ) AS conv_idx
                    FROM
                        conversations conv
                    WHERE
                        conv.user_id = ?
                )
                SELECT conv_id 
                FROM RankedConversations
                WHERE conv_idx = ?
                """,
                (int(user_id), int(conv_idx)),
            ).fetchone()

    def get_create_conv_id(self, user_id: int, conv_idx: int) -> int:
        conv_id = self.get_conv_id(user_id, conv_idx)
        log.debug(f"conv_id: {conv_id}")
        if conv_id is None:
            return self.new_conversation(user_id)
        return conv_id[0]


bump_conv_sql = """
                UPDATE conversations
                SET updated_at = datetime('now'), chat_count = chat_count + 1
                WHERE id = ?
                """

add_chat_sql = """
                INSERT INTO chats (conv_id, is_user, msg, timestamp)
                VALUES (?, ?, ?, datetime('now'))
                """
