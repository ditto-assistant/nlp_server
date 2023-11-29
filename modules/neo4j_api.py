import json
from neo4j import GraphDatabase

# TEST = """
# {
#   "nodes": [
#     {
#       "id": 0,
#       "type": "Prompt",
#       "title": "Prompt",
#       "description": "What is the best Pokémon?"
#     },
#     {
#       "id": 1,
#       "type": "Response",
#       "title": "Response",
#       "description": "As of January 2022, Arceus is considered the strongest Pokémon, but ongoing releases may introduce new contenders, so check official Pokémon sources for the latest information."
#     },
#     {
#       "id": 2,
#       "type": "Subject",
#       "title": "Pokémon",
#       "description": "Pokémon is a media franchise created by Satoshi Tajiri and owned by The Pokémon Company, created in 1995. It is centered on fictional creatures called 'Pokémon,' which humans known as Pokémon Trainers catch and train to battle each other for sport."
#     },
#     {
#       "id": 3,
#       "type": "Pokémon",
#       "title": "Arceus",
#       "description": "Arceus's legendary status is attributed to its extraordinary abilities and significance within the Pokémon lore. Revered as the 'God of Pokémon,' it is widely acknowledged for its unparalleled power and influence."
#     },
#     {
#       "id": 4,
#       "type": "Stats",
#       "title": "Base Stats",
#       "description": "Arceus's base stats surpass those of many other Pokémon, solidifying its reputation as a powerhouse within the Pokémon world. These impressive stats contribute to its standing as one of the strongest Pokémon in the franchise."
#     },
#     {
#       "id": 5,
#       "type": "Explanation",
#       "title": "Pokémon Franchise",
#       "description": "The Pokémon franchise is constantly evolving, with new games and generations introducing new and powerful Pokémon."
#     },
#     {
#       "id": 6,
#       "type": "Explanation",
#       "title": "Determining Strength",
#       "description": "The determination of the 'strongest' Pokémon is a nuanced process, considering factors such as individual stats, movesets, and type matchups."
#     },
#     {
#       "id": 7,
#       "type": "Explanation",
#       "title": "Staying Informed",
#       "description": "For the latest and most accurate information on the strongest Pokémon, it is highly recommended to consult the latest official Pokémon sources."
#     }
#   ],
#   "relationships": [
#     {
#       "src_node": 0,
#       "target_node": 1,
#       "relationship_type": "HAS_RESPONSE"
#     },
#     {
#       "src_node": 1,
#       "target_node": 2,
#       "relationship_type": "HAS_SUBJECT"
#     },
#     {
#       "src_node": 2,
#       "target_node": 3,
#       "relationship_type": "HAS_LEGENDARY_STATUS"
#     },
#     {
#       "src_node": 3,
#       "target_node": 4,
#       "relationship_type": "HAS_BASE_STATS_AND_SUPERIORITY"
#     },
#     {
#       "src_node": 2,
#       "target_node": 5,
#       "relationship_type": "EXISTS_IN_DYNAMIC_FRANCHISE"
#     },
#     {
#       "src_node": 4,
#       "target_node": 6,
#       "relationship_type": "FACTORS_INFLUENCING_STRENGTH"
#     },
#     {
#       "src_node": 2,
#       "target_node": 7,
#       "relationship_type": "REQUIRES_STAYING_INFORMED"
#     }
#   ]
# }
# """

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

import os

class Neo4jAPI:

    def __init__(self):
        self.latest_node = self.load_latest_node_id()

    def load_latest_node_id(self):
        if not os.path.exists("latest_node_id.json"):
            return {"id": 0}
        else:
            with open("latest_node_id.json", "r") as f:
                latest_node_id = json.load(f)
                latest_node_id['id'] = int(latest_node_id['id']) + 1
            return latest_node_id

    def update_latest_node_id(self):
        with open("latest_node_id.json", "w") as f:
            json.dump(self.latest_node, f)
    
    def create_graph(self, nodes, relationships):
        self.driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'), database='neo4j')
        for node in nodes:
            self.create_node(node)
        for relationship in relationships:
            self.create_relationship(relationship)
        latest_node_id = nodes[-1]["id"]
        self.latest_node["id"] = int(latest_node_id) + self.latest_node["id"]
        self.update_latest_node_id()
        self.driver.close()
        

    def create_node(self, node):
        node_id = int(node["id"]) + self.latest_node["id"]
        node_type = node["type"]
        node_title = node["title"]
        node_description = node["description"]
        self.driver.execute_query("""
            CREATE (:%s {title: "%s", description: "%s", id: %d})
        """ % (node_type, node_title, node_description, node_id))
    
    def create_relationship(self, relationship):
        src_node = relationship["src_node"] + self.latest_node["id"]
        target_node = relationship["target_node"] + self.latest_node["id"]
        relationship_type = relationship["relationship_type"]
        self.driver.execute_query("""
            MATCH (a), (b)
            WHERE a.id = %d AND b.id = %d
            CREATE (a)-[:%s]->(b)
        """ % (src_node, target_node, relationship_type))

if __name__ == "__main__":

    neo4j_api = Neo4jAPI()
    kg = json.loads(TEST)
    nodes = kg["nodes"]
    relationships = kg["relationships"]
    neo4j_api.create_graph(nodes, relationships)
