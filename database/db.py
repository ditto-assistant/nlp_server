import sqlite3
import json
import time


class DittoDB:
    """
    This class contains helper functions for operations around a user's database.
    """

    def __init__(self):
        pass

    def get_user_db_path(self, user_id: str) -> str:
        """
        This function returns the path to the user's database.
        param user_id: The user's id.
        return: The path to the user's database.
        """
        return f"database/{user_id}.db"

    def get_prompt_response_count(self, user_id: str) -> int:
        """
        This function returns the number of prompts and responses in the user's database.
        param user_id: The user's id.
        return: The number of prompts and responses in the user's database.
        """
        try:
            SQL = sqlite3.connect(self.get_user_db_path(user_id))
            cur = SQL.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS prompts(prompt VARCHAR, timestamp)")
            SQL.commit()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS responses(response VARCHAR, timestamp)"
            )
            SQL.commit()
            prompt_count = cur.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
            response_count = cur.execute("SELECT COUNT(*) FROM responses").fetchone()[0]
            SQL.close()
        except Exception as e:
            prompt_count = 0
            response_count = 0
        return int(prompt_count) + int(response_count)

    def get_conversation_history(self, user_id: str):
        def create_response_arrays(arr):
            response = dict()
            for ndx, x in enumerate(arr):
                response[str(ndx)] = [x[0], x[1]]
            return json.dumps(response)

        try:
            SQL = sqlite3.connect(self.get_user_db_path(user_id))
            cur = SQL.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS prompts(prompt VARCHAR, timestamp)")
            SQL.commit()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS responses(response VARCHAR, timestamp)"
            )
            SQL.commit()
            req = cur.execute("SELECT * FROM prompts")
            prompts = req.fetchall()
            SQL.commit()
            cur.execute("SELECT * FROM responses")
            responses = req.fetchall()
            SQL.commit()
            SQL.close()

            return create_response_arrays(prompts), create_response_arrays(responses)

        except Exception as e:
            prompts = []
            responses = []
            return None

    def reset_conversation(self, user_id: str):
        SQL = sqlite3.connect(self.get_user_db_path(user_id))
        cur = SQL.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS prompts(prompt VARCHAR, timestamp)")
        SQL.commit()
        cur.execute("CREATE TABLE IF NOT EXISTS responses(response VARCHAR, timestamp)")
        SQL.commit()
        cur.execute("DELETE FROM prompts")
        cur.execute("DELETE FROM responses")
        SQL.commit()
        SQL.close()

    def write_response_to_db(self, user_id: str, response: str):
        SQL = sqlite3.connect(self.get_user_db_path(user_id))
        cur = SQL.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS responses(response VARCHAR, timestamp)")
        SQL.commit()
        cur.execute(
            "INSERT INTO responses VALUES('%s', '%s')"
            % (response.replace("'", "''"), str(int(time.time())))
        )
        SQL.commit()
        SQL.close()

    def write_prompt_to_db(self, user_id: str, prompt: str):
        SQL = sqlite3.connect(self.get_user_db_path(user_id))
        cur = SQL.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS prompts(prompt VARCHAR, timestamp)")
        SQL.commit()
        cur.execute(
            "INSERT INTO prompts VALUES('%s', '%s')"
            % (prompt.replace("'", "''"), str(int(time.time())))
        )
        SQL.commit()
        SQL.close()
