'''
This is an LLM agent used to handle GOOGLE_SEARCH commands from Ditto Memory agent.
'''

from langchain.agents import load_tools
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.utilities import SerpAPIWrapper

# import logger
import logging

log = logging.getLogger("google_search_agent")
logging.basicConfig(level=logging.INFO)

from fallback_agent import GoogleSearchFallbackAgent

class GoogleSearchAgent():

    def __init__(self, verbose=False):
        self.initialize_agent(verbose)
    
    def initialize_agent(self, verbose):
        '''
        This function initializes the agent.
        '''
        llm = ChatOpenAI(temperature=0.4, model_name="gpt-3.5-turbo")
        search = SerpAPIWrapper()
        tools = [
            Tool(
                name="Intermediate Answer",
                func=search.run,
                description="useful for when you need to ask with search",
            )
        ]

        self.agent = initialize_agent(
            tools, llm, agent=AgentType.SELF_ASK_WITH_SEARCH, verbose=verbose)

        self.fallback = GoogleSearchFallbackAgent(verbose=verbose)        

    def handle_google_search(self, query):
        '''
        This function handles GOOGLE_SEARCH commands from Ditto Memory agent.
        '''
        try:
            response = self.agent.run(query)
        except Exception as e:
            log.info(f"Error running google search agent: {e}")
            log.info(f"Running fallback agent...")
            try:
                response = self.fallback.fallback_agent.run(query)
            except Exception as e:
                log.info(f"Error running fallback agent: {e}")
                response = f"Error running google search agent: {e}"
                if 'LLM output' in response:
                    response = response.split('`')[1]
            
        return response
    
if __name__ == "__main__":
    google_search_agent = GoogleSearchAgent(verbose=True)
    query = "Whats the weather like in New York?"
    response = google_search_agent.handle_google_search(query)
    log.info(f"Response: {response}")