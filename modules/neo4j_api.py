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

TEST = """
{
  "nodes": [
    {
      "id": 0,
      "type": "Prompt",
      "title": "Prompt",
      "description": "What is the capital of France?"
    },
    {
      "id": 1,
      "type": "Response",
      "title": "Response",
      "description": "The capital of France is Paris."
    },
    {
      "id": 2,
      "type": "Subject",
      "title": "France",
      "description": "France is a country located in Western Europe. It is known for its rich history, culture, and contributions to art, fashion, and cuisine."
    },
    {
      "id": 3,
      "type": "Capital",
      "title": "Paris",
      "description": "Paris is the capital and largest city of France. It is a global center for art, fashion, gastronomy, and culture."
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
      "relationship_type": "ASKS_ABOUT_SUBJECT"
    },
    {
      "src_node": 2,
      "target_node": 3,
      "relationship_type": "HAS_CAPITAL"
    }
  ]
}
"""

TEST = """
{
  "nodes": [
    {
      "id": 0,
      "type": "Prompt",
      "title": "Prompt",
      "description": "Can you tell me about the pokemon Mewtwo?"
    },
    {
      "id": 1,
      "type": "Response",
      "title": "Response",
      "description": "Mewtwo is a powerful Psychic-type Pokémon that was created through genetic manipulation. It possesses extraordinary psychic abilities, an imposing appearance, and has made appearances in various Pokémon media. Stay updated with official Pokémon sources for the latest information on Mewtwo."
    },
    {
      "id": 2,
      "type": "Subject",
      "title": "Mewtwo",
      "description": "Mewtwo is a powerful Psychic-type Pokémon that was created through genetic manipulation. It is renowned for its extraordinary psychic abilities and exceptional intelligence. This Pokémon is a clone of the legendary Pokémon Mew, and it was specifically engineered with the ambition of becoming the most dominant and formidable Pokémon in existence."
    },
    {
      "id": 3,
      "type": "Appearance",
      "title": "Physical Appearance",
      "description": "Mewtwo possesses a sleek and humanoid physique, characterized by its vibrant purple fur. It boasts a long, elegant tail and a distinctive, heavily armored head. These physical attributes contribute to Mewtwo's imposing presence and visually distinguish it from other Pokémon."
    },
    {
      "id": 4,
      "type": "Psychic Abilities",
      "title": "Psychic Abilities",
      "description": "Mewtwo's psychic capabilities are unparalleled within the Pokémon world. It possesses an array of psychic powers, including telekinesis, telepathy, and the ability to manipulate energy. These abilities grant Mewtwo an immense advantage in battles and make it a formidable opponent."
    },
    {
      "id": 5,
      "type": "Origin and Creation",
      "title": "Origin and Creation",
      "description": "Mewtwo's origin lies in its genetic connection to the legendary Pokémon Mew. Scientists conducted extensive genetic experiments to create a clone of Mew, resulting in the birth of Mewtwo. The aim of these experiments was to produce a Pokémon with unparalleled power and abilities."
    },
    {
      "id": 6,
      "type": "Media Appearances",
      "title": "Appearances in Media",
      "description": "Mewtwo has made appearances in various Pokémon games, movies, and TV shows. It is often depicted as a significant character and a formidable adversary. Its presence in these media outlets has contributed to its popularity and recognition among Pokémon enthusiasts."
    },
    {
      "id": 7,
      "type": "Legacy and Impact",
      "title": "Legacy and Impact",
      "description": "Mewtwo's status as a powerful and iconic Pokémon has solidified its place in the Pokémon franchise. Its unique abilities, captivating appearance, and intriguing backstory have made it a fan favorite and a symbol of strength and intelligence within the Pokémon universe."
    },
    {
      "id": 8,
      "type": "Ongoing Evolution",
      "title": "Ongoing Evolution",
      "description": "As the Pokémon franchise continues to evolve with new games and generations, Mewtwo's role and significance may undergo further development. It is essential to stay updated with the latest official Pokémon sources to remain informed about any new information or changes regarding Mewtwo."
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
      "relationship_type": "HAS_APPEARANCE"
    },
    {
      "src_node": 2,
      "target_node": 4,
      "relationship_type": "HAS_PSYCHIC_ABILITIES"
    },
    {
      "src_node": 2,
      "target_node": 5,
      "relationship_type": "HAS_ORIGIN_AND_CREATION"
    },
    {
      "src_node": 2,
      "target_node": 6,
      "relationship_type": "HAS_MEDIA_APPEARANCES"
    },
    {
      "src_node": 2,
      "target_node": 7,
      "relationship_type": "HAS_LEGACY_AND_IMPACT"
    },
    {
      "src_node": 2,
      "target_node": 8,
      "relationship_type": "HAS_ONGOING_EVOLUTION"
    }
  ]
}
"""

import os


class Neo4jAPI:
    def __init__(self):
        self.latest_node = self.load_latest_node_id()
        self.users_obj = self.load_users()

    def load_latest_node_id(self):
        if not os.path.exists("latest_node_id.json"):
            return {"id": 0}
        else:
            with open("latest_node_id.json", "r") as f:
                latest_node_id = json.load(f)
                latest_node_id["id"] = int(latest_node_id["id"]) + 1
            return latest_node_id

    def load_users(self):
        if not os.path.exists("kg_users.json"):
            return {"users": []}
        else:
            with open("kg_users.json", "r") as f:
                users_obj = json.load(f)
            return users_obj

    def update_user_ids(self, user_name, user_id):
        self.users_obj["users"].append({user_id: user_name})
        with open("kg_users.json", "w") as f:
            json.dump(self.users_obj, f)

    def get_user_id(self, user_name):
        for user_obj in self.users_obj["users"]:
            user_id = list(user_obj.keys())[0]
            user_name_ = user_obj[user_id]
            if user_name_ == user_name:
                return int(user_id)
        return None

    def update_latest_node_id(self):
        with open("latest_node_id.json", "w") as f:
            json.dump(self.latest_node, f)

    def user_id_exists(self, user_id):
        for user in self.users_obj["users"]:
            if user[user_id]:
                return True
        return False

    def create_user_node(self, user_name):
        random_id = -np.random.randint(1, 1000000000)
        while self.user_id_exists(random_id):
            random_id = -np.random.randint(1, 1000000000)
        self.driver.execute_query(
            """
            CREATE (:%s {name: "%s", id: %d})
        """
            % ("User", user_name, random_id)
        )
        self.update_user_ids(user_name, random_id)

    def create_graph(self, user_name, nodes, relationships):
        try:
            self.driver = GraphDatabase.driver(
                "bolt://localhost:7687", auth=("neo4j", "password"), database="neo4j"
            )
            user_node_id = self.get_user_id(user_name)
            if user_node_id is None:
                self.create_user_node(user_name)
                user_node_id = self.get_user_id(user_name)
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
        relationship_type = relationship["relationship_type"]
        self.driver.execute_query(
            """
            MATCH (a), (b)
            WHERE a.id = %d AND b.id = %d
            CREATE (a)-[:%s]->(b)
        """
            % (src_node, target_node, relationship_type)
        )


if __name__ == "__main__":
    neo4j_api = Neo4jAPI()
    kg = json.loads(TEST)
    nodes = kg["nodes"]
    relationships = kg["relationships"]
    neo4j_api.create_graph("Omar", nodes, relationships)
