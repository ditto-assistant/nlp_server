"""
This class will start a thread that takes a prompt and response pair and runs it through the wikifier
agent and then the knowlege graph agent. The returned json from the KG agent will be written to neo4j
via the neo4j driver. The thread will stop when the job is complete or when the thread is stopped.
"""

from threading import Thread
import time
import logging
import json
import os

from modules.wikifier_agent import WikifierAgent
from modules.knowledge_graph_agent import KGAgent

from modules.neo4j_api import Neo4jAPI

log = logging.getLogger("kg_job")
log.setLevel(logging.INFO)


class KGJob:
    def __init__(self, user_name, prompt, response):
        self.user_name = user_name
        self.prompt = prompt
        self.response = response
        self.wikifier_agent = WikifierAgent()
        self.kg_agent = KGAgent()
        self.neo4j_api = Neo4jAPI(
            user_name=user_name,
        )
        self.thread = Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        print("KG job started")
        wikifier_res = self.wikifier_agent.wikify(self.prompt, self.response)
        if len(wikifier_res.strip()) < 10 or wikifier_res.strip().lower() == "no.":
            print("No wikifier results")
            return
        kg_res = self.kg_agent.construct_kg(self.prompt, wikifier_res).strip("```").strip("```json")
        try:
            kg_res = json.loads(kg_res)
        except BaseException as e:
            log.error(e)
        nodes = kg_res["nodes"]
        relationships = kg_res["relationships"]
        self.neo4j_api.create_graph(nodes, relationships)
        print("KG job finished")

    def is_alive(self):
        return self.thread.is_alive()

    def stop(self):
        self.thread.join()
        log.info("KG job stopped")


if __name__ == "__main__":
    prompt = "Tell me a short story about a dog."
    response = "Once upon a time, there was a dog named Ditto. He was a very good dog."
    kg_job = KGJob("Omar", prompt, response)
