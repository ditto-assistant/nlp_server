'''
This is an LLM agent used to handle GOOGLE_SEARCH commands from Ditto Memory agent.
'''

from langchain.agents import load_tools
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.utilities import SerpAPIWrapper

# load env
from dotenv import load_dotenv
load_dotenv()

# import logger
import logging

log = logging.getLogger("google_search_agent")
logging.basicConfig(level=logging.INFO)

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
        
        fallback_agent_tools = load_tools(["google-serper"], llm=llm)
        self.fallback_agent = initialize_agent(
            fallback_agent_tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION , verbose=verbose)

    def handle_google_search(self, query):
        '''
        This function handles GOOGLE_SEARCH commands from Ditto Memory agent.
        '''
        try:
            response = self.agent.run(query)
        except Exception as e:
            log.info(f"Error running google search agent: {e}")
            log.info(f"Running fallback agent: {e}")
            try:
                response = self.fallback_agent.run(query)
            except Exception as e:
                log.info(f"Error running fallback agent: {e}")
                response = f"Error running google search agent: {e}"
                if 'LLM output' in response:
                    response = response.split('`')[1]
            
        return response
    
if __name__ == "__main__":
    google_search_agent = GoogleSearchAgent(verbose=True)
    query = "What's the weather in New York?"
    response = google_search_agent.handle_google_search(query)
    log.info(f"Response: {response}")