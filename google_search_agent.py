'''
This is an LLM agent used to handle GOOGLE_SEARCH commands from Ditto Memory agent.
'''

from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

# import logger
import logging

log = logging.getLogger("google_search_agent")
logging.basicConfig(level=logging.INFO)

class GoogleSearchAgent():

    def __init__(self):
        self.initialize_agent()
    
    def initialize_agent(self):
        '''
        This function initializes the agent.
        '''
        llm = ChatOpenAI(temperature=0.4, model_name="gpt-3.5-turbo")
        tools = load_tools(["google-serper"], llm=llm)
        self.agent = initialize_agent(
            tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=False
        )

    def handle_google_search(self, query):
        '''
        This function handles GOOGLE_SEARCH commands from Ditto Memory agent.
        '''
        try:
            response = self.agent.run(query)
        except Exception as e:
            log.info(f"Error running google search agent: {e}")
            response = f"Error running google search agent: {e}"
            if 'LLM output' in response:
                response = response.split('`')[1]
            
        return response
    
