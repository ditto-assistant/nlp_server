"""
This is an LLM agent used to handle GOOGLE_SEARCH commands from Ditto Memory agent.
"""

from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.llms import HuggingFaceHub
from langchain.utilities import GoogleSerperAPIWrapper

import logging
import os

log = logging.getLogger("google_search_fallback_agent")
logging.basicConfig(level=logging.INFO)

# load env
from dotenv import load_dotenv

load_dotenv()

LLM = os.environ.get("LLM")


class GoogleSearchFallbackAgent:
    def __init__(self, verbose=False):
        self.initialize_agent(verbose)

    def initialize_agent(self, verbose):
        """
        This function initializes the agent.
        """
        if LLM == "openai":
            llm = ChatOpenAI(temperature=0.4, model_name="gpt-3.5-turbo")
        else:
            repo_id = "codellama/CodeLlama-13b-hf"
            llm = HuggingFaceHub(
                repo_id=repo_id, model_kwargs={"temperature": 0.5, "max_length": 3000}
            )

        fallback_agent_tools = load_tools(["google-serper"], llm=llm)
        self.search = GoogleSerperAPIWrapper()
        self.fallback_agent = initialize_agent(
            fallback_agent_tools,
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=verbose,
        )

    def handle_google_search(self, query):
        """
        This function handles GOOGLE_SEARCH commands from Ditto Memory agent.
        """
        try:
            response = self.fallback_agent.run(query)
        except Exception as e:
            log.info(f"Error running fallback agent: {e}")
            response = f"Error running google search agent: {e}"
            if "LLM output" in response:
                response = response.split("`")[1]

        return response


if __name__ == "__main__":
    google_search_agent = GoogleSearchFallbackAgent(verbose=True)
    query = "What is steeve job's birthday?"
    response = google_search_agent.handle_google_search(query)
    log.info(f"Response: {response}")
