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

log = logging.getLogger("ditto_memory")
logging.basicConfig(level=logging.DEBUG)

TEMPLATE = """The following is a conversation between an AI named Ditto and a human that are best friends. Ditto is helpful and answers factual questions correctly but maintains a friendly relationship with the human.

Relevant pieces from past memories with the user:
{history}

(You do not need to use these past memories if not relevant)

Current conversation:
{input}
Ditto:"""


class DittoMemory:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.4, model_name="gpt-3.5-turbo-16k")
        self.memory = {}

    def __create_load_memory(self, reset=False, user_id="ditto"):
        mem_dir = f"memory/{user_id}"
        mem_file = f"{mem_dir}/ditto_memory.pkl"
        if not os.path.exists(mem_dir):
            os.makedirs(mem_dir)
            log.debug(f"Created memory directory for {user_id}")
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
            log.debug(f"Created memory file for {user_id}")
        else:
            self.memory[user_id] = pickle.load(open(mem_file, "rb"))
            log.debug(f"Loaded memory file for {user_id}")

    def save_new_memory(self, prompt, response, user_id="ditto"):
        self.__create_load_memory(user_id=user_id)
        mem_dir = f"memory/{user_id}"
        mem_file = f"{mem_dir}/ditto_memory.pkl"
        self.memory[user_id].save_context({"input": prompt}, {"output": response})
        pickle.dump(self.memory[user_id], open(mem_file, "wb"))
        log.debug(f"Saved new memory for {user_id}")

    def reset_memory(self, user_id="ditto"):
        self.__create_load_memory(reset=True, user_id=user_id)
        log.debug(f"Reset memory for {user_id}")

    def prompt(self, query, user_id="ditto"):
        self.__create_load_memory(user_id=user_id)
        stamp = str(datetime.utcfromtimestamp(time.time()))
        if "<STMEM>" in query:
            raw_query = query.split("<STMEM>")[2]
            mem_query = f"Timestamp: {stamp}\nHuman: {raw_query}"
            query = query.split("<STMEM>")[1] + "\nCurrent Prompt: " + mem_query
        else:
            # embed timestamps to query
            query = f"Timestamp: {stamp}\nHuman: {query}"
            mem_query = query

        prompt = PromptTemplate(input_variables=["history", "input"], template=TEMPLATE)
        conversation_with_memory = ConversationChain(
            llm=self.llm, prompt=prompt, memory=self.memory[user_id], verbose=False
        )
        res = conversation_with_memory.predict(input=query)
        self.save_new_memory(mem_query, res, user_id)
        log.debug(f"Handled prompt for {user_id}")
        return res


if __name__ == "__main__":
    ditto = DittoMemory()
