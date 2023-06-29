from datetime import datetime
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.memory import VectorStoreRetrieverMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
import faiss
from langchain.docstore import InMemoryDocstore
from langchain.vectorstores import FAISS


# class DittoMemory:
#     def __init__(self):

embedding_size = 1536  # Dimensions of the OpenAIEmbeddings
index = faiss.IndexFlatL2(embedding_size)
embedding_fn = OpenAIEmbeddings().embed_query
vectorstore = FAISS(embedding_fn, index, InMemoryDocstore({}), {})

# In actual usage, you would set `k` to be a higher value, but we use k=1 to show that
# the vector lookup still returns the semantically relevant information
retriever = vectorstore.as_retriever(search_kwargs=dict(k=1))
memory = VectorStoreRetrieverMemory(retriever=retriever)

# When added to an agent, the memory object can save pertinent information from conversations or used tools
memory.save_context({"input": "Hi! What's up? My name is Omar!"}, {
                    "output": "Hi Omar! My name is Ditto. Nice to meet you!"})
memory.save_context(
    {"input": "Hey Ditto! Nice to meet you too. Glad we can be talking."}, {"output": "Me too!"})
memory.save_context({"input": "I love making music and programming as my hobbies"}, {
                    "output": "Cool! Those are some great hobbies. What kind of music and programs do you make?"})

llm = OpenAI(temperature=0)  # Can be any valid LLM
_DEFAULT_TEMPLATE = """The following is a conversation between an AI named Ditto and a human that are best friends. Ditto is helpful and answers factual questions correctly but maintains a friendly relationship with the human.

Relevant pieces from past memories with the user:
{history}

(You do not need to use these past memories if not relevant)

Current conversation:
Human: {input}
Ditto:"""
PROMPT = PromptTemplate(
    input_variables=["history", "input"], template=_DEFAULT_TEMPLATE
)

conversation_with_summary = ConversationChain(
    llm=llm,
    prompt=PROMPT,
    memory=memory,
    verbose=True
)

res = conversation_with_summary.predict(
    input="What did I tell you my favorite hobbies were?")

print(res)
