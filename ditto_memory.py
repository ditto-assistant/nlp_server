from datetime import datetime
import os
import pickle
import time
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.memory import VectorStoreRetrieverMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
import faiss
from langchain.docstore import InMemoryDocstore
from langchain.vectorstores import FAISS

TEMPLATE = """The following is a conversation between an AI named Ditto and a human that are best friends. Ditto is helpful and answers factual questions correctly but maintains a friendly relationship with the human.

Relevant pieces from past memories with the user:
{history}

(You do not need to use these past memories if not relevant)

Current conversation:
{input}
Ditto:"""


class DittoMemory:
    def __init__(self):
        self.llm = OpenAI(temperature=0)
        self.__create_load_memory()

    def __create_load_memory(self, reset=False):
        if not os.path.exists('memory'):
            os.mkdir('memory')
        if not os.path.exists('memory/ditto_memory.pkl') or reset:

            embedding_size = 1536  # Dimensions of the OpenAIEmbeddings
            index = faiss.IndexFlatL2(embedding_size)
            embedding_fn = OpenAIEmbeddings().embed_query
            vectorstore = FAISS(embedding_fn, index, InMemoryDocstore({}), {})
            retriever = vectorstore.as_retriever(search_kwargs=dict(k=10))
            memory = VectorStoreRetrieverMemory(retriever=retriever)

            memory.save_context({"input": "Hi! What's up? "}, {
                "output": "Hi! My name is Ditto. Nice to meet you!"})
            memory.save_context(
                {"input": "Hey Ditto! Nice to meet you too. Glad we can be talking."}, {"output": "Me too!"})
            pickle.dump(memory, open('memory/ditto_memory.pkl', 'wb'))
            self.memory = memory
        else:
            self.memory = pickle.load(open('memory/ditto_memory.pkl', 'rb'))

    def save_new_memory(self, prompt, response):
        self.memory.save_context({"input": prompt}, {
            "output": response})
        pickle.dump(self.memory, open('memory/ditto_memory.pkl', 'wb'))

    def reset_memory(self):
        self.__create_load_memory(reset=True)

    def prompt(self, query):

        stamp = str(datetime.utcfromtimestamp(time.time()/1e3))
        # embed timestamps to query
        query = f'Timestamp: {stamp}\nHuman: {query}'

        prompt = PromptTemplate(
            input_variables=["history", "input"], template=TEMPLATE
        )

        conversation_with_memory = ConversationChain(
            llm=self.llm,
            prompt=prompt,
            memory=self.memory,
            verbose=False
        )

        res = conversation_with_memory.predict(
            input=query)

        self.save_new_memory(query, res)

        return res


if __name__ == "__main__":
    ditto = DittoMemory()
