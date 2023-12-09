import json
from neo4j import GraphDatabase
import numpy as np

TEST = """
{
  "nodes": [
    {
      "id": 0,
      "type": "Prompt",
      "title": "Prompt",
      "description": "What is the best Pokémon?"
    },
    {
      "id": 1,
      "type": "Response",
      "title": "Response",
      "description": "As of January 2022, Arceus is considered the strongest Pokémon, but ongoing releases may introduce new contenders, so check official Pokémon sources for the latest information."
    },
    {
      "id": 2,
      "type": "Subject",
      "title": "Pokémon",
      "description": "Pokémon is a media franchise created by Satoshi Tajiri and owned by The Pokémon Company, created in 1995. It is centered on fictional creatures called 'Pokémon,' which humans known as Pokémon Trainers catch and train to battle each other for sport."
    },
    {
      "id": 3,
      "type": "Pokémon",
      "title": "Arceus",
      "description": "Arceus's legendary status is attributed to its extraordinary abilities and significance within the Pokémon lore. Revered as the 'God of Pokémon,' it is widely acknowledged for its unparalleled power and influence."
    },
    {
      "id": 4,
      "type": "Stats",
      "title": "Base Stats",
      "description": "Arceus's base stats surpass those of many other Pokémon, solidifying its reputation as a powerhouse within the Pokémon world. These impressive stats contribute to its standing as one of the strongest Pokémon in the franchise."
    },
    {
      "id": 5,
      "type": "Explanation",
      "title": "Pokémon Franchise",
      "description": "The Pokémon franchise is constantly evolving, with new games and generations introducing new and powerful Pokémon."
    },
    {
      "id": 6,
      "type": "Explanation",
      "title": "Determining Strength",
      "description": "The determination of the 'strongest' Pokémon is a nuanced process, considering factors such as individual stats, movesets, and type matchups."
    },
    {
      "id": 7,
      "type": "Explanation",
      "title": "Staying Informed",
      "description": "For the latest and most accurate information on the strongest Pokémon, it is highly recommended to consult the latest official Pokémon sources."
    }
  ],
  "relationships": [
    {
      "src_node": 0,
      "target_node": 1,
      "relationship_type": "HAS_RESPONSE"
    },
    {
      "src_node": 1,
      "target_node": 2,
      "relationship_type": "HAS_SUBJECT"
    },
    {
      "src_node": 2,
      "target_node": 3,
      "relationship_type": "HAS_LEGENDARY_STATUS"
    },
    {
      "src_node": 3,
      "target_node": 4,
      "relationship_type": "HAS_BASE_STATS_AND_SUPERIORITY"
    },
    {
      "src_node": 2,
      "target_node": 5,
      "relationship_type": "EXISTS_IN_DYNAMIC_FRANCHISE"
    },
    {
      "src_node": 4,
      "target_node": 6,
      "relationship_type": "FACTORS_INFLUENCING_STRENGTH"
    },
    {
      "src_node": 2,
      "target_node": 7,
      "relationship_type": "REQUIRES_STAYING_INFORMED"
    }
  ]
}
"""

import os


class Neo4jAPI:
    def __init__(self, user_name="Human"):
        self.user_name = user_name
        self.memory_dir = self.init_memory_dirs()
        self.latest_node = self.load_latest_node_id()
        self.users_obj = self.load_user()
        self.load_db_params()

    def load_db_params(self):
        self.neo4j_host = os.getenv("NEO4J_URI", "localhost:7687")
        self.neo4j_username = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

    def init_memory_dirs(self):
        if not os.path.exists(f"memory/{self.user_name}"):
            os.mkdir(f"memory/{self.user_name}")
        return f"memory/{self.user_name}"

    def load_latest_node_id(self):
        if not os.path.exists(f"{self.memory_dir}/latest_node_id.json"):     
            return {"id": 0}   
        else:
            with open(f"{self.memory_dir}/latest_node_id.json", "r") as f:
                latest_node_id = json.load(f)
                latest_node_id["id"] = int(latest_node_id["id"]) + 1
            return latest_node_id

    def load_user(self):
        if not os.path.exists(f"{self.memory_dir}/kg_users.json"):
            return {"users": [{'-1': 'Ditto'}]}
        else:
            with open(f"{self.memory_dir}/kg_users.json", "r") as f:
                users_obj = json.load(f)
            return users_obj

    def update_user_ids(self, user_id):
        self.users_obj["users"].append({user_id: self.user_name})
        with open(f"{self.memory_dir}/kg_users.json", "w") as f:
            json.dump(self.users_obj, f)

    def get_user_id(self):
        for user_obj in self.users_obj["users"]:
            user_id = list(user_obj.keys())[0]
            user_name_ = user_obj[user_id]
            if user_name_ == self.user_name:
                return int(user_id)
        return None

    def update_latest_node_id(self):
        with open(f"{self.memory_dir}/latest_node_id.json", "w") as f:
            json.dump(self.latest_node, f)

    def user_id_exists(self, user_id):
        for user in self.users_obj["users"]:
            if user_id in user.keys():
                return True
        return False

    def create_user_node(self):
        random_id = -np.random.randint(10000, 1000000000)
        while self.user_id_exists(random_id):
            random_id = -np.random.randint(10000, 1000000000)
        self.driver.execute_query(
            """
            CREATE (:%s {name: "%s", id: %d})
        """
            % ("User", self.user_name, random_id)
        )
        self.update_user_ids(random_id)
        return random_id

    def create_graph(self, nodes, relationships):
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_host, auth=(self.neo4j_username, self.neo4j_password), database='neo4j'
            )
            user_node_id = self.get_user_id()
            if user_node_id == None:
                user_node_id = self.create_user_node()
                self.latest_node["id"] = self.latest_node["id"] + int(np.abs(user_node_id)*0.50)
            for node in nodes:
                self.create_node(node)
            for relationship in relationships:
                self.create_relationship(relationship)

            # connect graph to user node
            prompt_node_id = nodes[0]["id"] + self.latest_node["id"]

            self.driver.execute_query(
                """
              MATCH (a), (b)
              WHERE a.id = %d AND b.id = %d
              CREATE (a)-[:%s]->(b)
          """
                % (user_node_id, prompt_node_id, "HAS_PROMPT")
            )

            latest_node_id = nodes[-1]["id"]
            self.latest_node["id"] = int(latest_node_id) + self.latest_node["id"]
            self.update_latest_node_id()

            self.driver.close()

        except BaseException as e:
            print(e)
            self.driver.close()

    def create_node(self, node):
        node_id = int(node["id"]) + self.latest_node["id"]
        node_type = str(node["type"]).replace(" ", "").strip()

        # replace all ASCII leaving only alphanumeric characters in node type
        node_type = "".join([c for c in node_type if c.isalnum()]) 

        node_title = node["title"]
        node_description = node["description"]
        self.driver.execute_query(
            """
            CREATE (:%s {title: "%s", description: "%s", id: %d})
        """
            % (node_type, node_title, node_description, node_id)
        )

    def create_relationship(self, relationship):
        src_node = relationship["src_node"] + self.latest_node["id"]
        target_node = relationship["target_node"] + self.latest_node["id"]
        relationship_type = str(relationship["relationship_type"]).replace("-", "_")

        self.driver.execute_query(
            """
            MATCH (a), (b)
            WHERE a.id = %d AND b.id = %d
            CREATE (a)-[:%s]->(b)
        """
            % (src_node, target_node, relationship_type)
        )


if __name__ == "__main__":
    neo4j_api = Neo4jAPI("Omar")
    kg = json.loads(TEST)
    nodes = kg["nodes"]
    relationships = kg["relationships"]
    neo4j_api.create_graph(nodes, relationships)
