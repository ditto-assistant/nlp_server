from datetime import datetime
import os
import pickle
import time
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.memory import VectorStoreRetrieverMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
import faiss
from langchain.docstore import InMemoryDocstore
from langchain.vectorstores import FAISS
import logging

# import google search agent
from google_search_agent import GoogleSearchAgent

log = logging.getLogger("ditto_memory")
logging.basicConfig(level=logging.INFO)

from templates.llm_tools import LLM_TOOLS_TEMPLATE
from templates.default import DEFAULT_TEMPLATE

# check is SERPER_API_KEY is set in os.environ
if "SERPER_API_KEY" not in os.environ:
    log.info("SERPER_API_KEY not set in os.environ... Loading default template")
    TEMPLATE = DEFAULT_TEMPLATE
else:
    log.info("Found SERPER_API_KEY. Loading LLM Tools template")
    TEMPLATE = LLM_TOOLS_TEMPLATE

class DittoMemory:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.4, model_name="gpt-3.5-turbo-16k")
        self.google_search_agent = GoogleSearchAgent()
        self.memory = {}

    def __create_load_memory(self, reset=False, user_id="ditto"):
        mem_dir = f"memory/{user_id}"
        mem_file = f"{mem_dir}/ditto_memory.pkl"
        if not os.path.exists(mem_dir):
            os.makedirs(mem_dir)
            log.info(f"Created memory directory for {user_id}")
        if not os.path.exists(mem_file) or reset:
            embedding_size = 1536  # Dimensions of the OpenAIEmbeddings
            index = faiss.IndexFlatL2(embedding_size)
            embedding_fn = OpenAIEmbeddings().embed_query
            vectorstore = FAISS(embedding_fn, index, InMemoryDocstore({}), {})
            retriever = vectorstore.as_retriever(search_kwargs=dict(k=5))
            self.memory[user_id] = VectorStoreRetrieverMemory(retriever=retriever)
            self.memory[user_id].save_context(
                {"input": "Hi! What's up? "},
                {"output": "Hi! My name is Ditto. Nice to meet you!"},
            )
            self.memory[user_id].save_context(
                {"input": "Hey Ditto! Nice to meet you too. Glad we can be talking."},
                {"output": "Me too!"},
            )
            pickle.dump(self.memory[user_id], open(mem_file, "wb"))
            log.info(f"Created memory file for {user_id}")
        else:
            self.memory[user_id] = pickle.load(open(mem_file, "rb"))
            log.info(f"Loaded memory file for {user_id}")

    def save_new_memory(self, prompt, response, user_id="ditto"):
        self.__create_load_memory(user_id=user_id)
        mem_dir = f"memory/{user_id}"
        mem_file = f"{mem_dir}/ditto_memory.pkl"
        self.memory[user_id].save_context({"input": prompt}, {"output": response})
        pickle.dump(self.memory[user_id], open(mem_file, "wb"))
        log.info(f"Saved new memory for {user_id}")

    def reset_memory(self, user_id="ditto"):
        self.__create_load_memory(reset=True, user_id=user_id)
        log.info(f"Reset memory for {user_id}")

    def prompt(self, query, user_id="ditto"):
        self.__create_load_memory(user_id=user_id)
        stamp = str(datetime.utcfromtimestamp(time.time()))
        if user_id=="ditto": user_id = "Human" # default to human if user_id is not provided
        if "<STMEM>" in query:
            raw_query = query.split("<STMEM>")[2]
            mem_query = f"Timestamp: {stamp}\n{user_id}: {raw_query}"
            query = query.split("<STMEM>")[1] + "\nCurrent Prompt: " + mem_query
        else:
            # embed timestamps to query
            query = f"Timestamp: {stamp}\n{user_id}: {query}"
            mem_query = query

        prompt = PromptTemplate(input_variables=["history", "input"], template=TEMPLATE)
        conversation_with_memory = ConversationChain(
            llm=self.llm, prompt=prompt, memory=self.memory[user_id], verbose=False
        )
        res = conversation_with_memory.predict(input=query)

        if "GOOGLE_SEARCH" in res:
            log.info(f"Handling prompt for {user_id} with Google Search Agent")
            ditto_command = '<GOOGLE_SEARCH>'
            ditto_query = res.split("GOOGLE_SEARCH")[-1].strip()
            res = self.google_search_agent.handle_google_search(res)
            res = res + '\n-LLM Tools: Google Search-' 
            memory_res = f'{ditto_command} {ditto_query} \nGoogle Search Agent: ' + res
        else:
            memory_res = res

        self.save_new_memory(mem_query, memory_res, user_id)
        log.info(f"Handled prompt for {user_id}")
        return res


if __name__ == "__main__":
    ditto = DittoMemory()
