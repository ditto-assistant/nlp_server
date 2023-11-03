import logging
import sqlite3
import json
import time

# setup logging for this module
log = logging.getLogger("db")
log.setLevel(logging.INFO)


class DittoDB:
    """
    This class contains helper functions for operations around a user's database.
    """

    def __init__(self):
        self.SQL = sqlite3.connect("database/ditto.db")
        self.run_sql_file("database/create_tables.sqlite")
        version = (
            self.SQL.cursor()
            .execute("SELECT id FROM migrations ORDER BY id desc LIMIT 1")
            .fetchone()[0]
        )
        log.info(f"Connected to ditto.db! version: {version}")

    def run_sql_file(self, file_path: str):
        """
        This function runs a sql file.
        param file_path: The path to the sql file.
        """
        with open(file_path, "r") as f:
            self.SQL.cursor().executescript(f.read())

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

    def get_conversation(
        self, user_id: int, conv_id: int, offset: int, limit: int, is_asc: bool
    ):
        order = "ASC" if is_asc else "DESC"
        return (
            self.SQL.cursor()
            .execute(
                f"SELECT id, timestamp, prompt, response FROM chats WHERE conv_id = ? ORDER BY timestamp {order} LIMIT ? OFFSET ?",
                (conv_id, limit, offset),
            )
            .fetchall()
        )

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

    def new_conversation(self, user_id: int):
        """
        This function creates a new conversation for the user.
        param user_id: The user's id.
        return: The conversation id.
        """
        result = self.SQL.cursor().execute(
            """
            INSERT INTO conversations (user_id, created_at, updated_at, viewed_at)
            VALUES (?, datetime('now'), datetime('now'), datetime('now'))
            """,
            (user_id),
        )
        self.SQL.commit()

    def write_prompt_to_db(self, user_id: int, prompt: str):
        conv_id = self.latest_id("conversations", "user_id", user_id)
        log.info(f"Writing prompt to db: {prompt}")
        result = self.SQL.cursor().execute(
            """
            INSERT INTO chats (conv_id, prompt, timestamp)
            VALUES(?, ?, datetime('now'))
            """,
            (conv_id, prompt),
        )
        self.SQL.commit()

    def write_response_to_latest_prompt(self, user_id: int, response: str):
        conv_id = self.latest_id("conversations", "user_id", user_id)
        chat_id = self.latest_id("chats", "conv_id", conv_id)
        self.SQL.cursor().execute(
            """
            UPDATE chats 
            SET response = ?
            WHERE id = ?
            """,
            (response, chat_id),
        )
        self.SQL.commit()

    def latest_id(self, table: str, ref_id_field: str, ref_id: str) -> int:
        """
        Returns the latest primary key ID for a given reference ID in a specified table.

        Args:
            table (str): The name of the table to search.
            ref_id_field (str): The name of the reference ID field in the table.
            ref_id (str): The reference ID to search for.

        Returns:
            int: The latest primary key ID for the given reference ID.
        """
        return (
            self.SQL.cursor()
            .execute(
                f"SELECT id FROM {table} WHERE {ref_id_field} = ? ORDER BY id DESC LIMIT 1",
                (ref_id,),
            )
            .fetchone()[0]
        )
