# LangChain Python Documentation

LangChain is a comprehensive framework for developing applications powered by large language models (LLMs). It provides a unified interface for working with various LLM providers, enabling developers to build sophisticated applications that leverage the capabilities of modern AI models. The framework simplifies every stage of the LLM application lifecycle, from initial development through productionization and deployment.

The framework consists of multiple open-source libraries that work together seamlessly. At its core, `langchain-core` provides base abstractions for chat models and other components, while integration packages offer lightweight, provider-specific implementations. The main `langchain` package contains chains, agents, and retrieval strategies for building complex applications, while `langgraph` provides orchestration capabilities with state management, persistence, and streaming. LangChain integrates with hundreds of providers and implements standard interfaces for language models, embedding models, vector stores, and related technologies.

## Chat Model Initialization

Initialize any chat model from supported providers using a unified interface.

```python
import getpass
import os

# Set up API key
if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")

from langchain.chat_models import init_chat_model

# Initialize chat model
model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

# Invoke model with a message
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content="Translate the following from English into Italian"),
    HumanMessage(content="hi!"),
]

response = model.invoke(messages)
print(response.content)  # Output: "Ciao!"

# Alternative invocation methods
response = model.invoke("Hello")  # Using string
response = model.invoke([{"role": "user", "content": "Hello"}])  # Using dict
response = model.invoke([HumanMessage("Hello")])  # Using message object
```

## Streaming Chat Responses

Stream output token-by-token from chat models for real-time responses.

```python
from langchain_anthropic.chat_models import ChatAnthropic

chat = ChatAnthropic(model="claude-3-haiku-20240307")

# Synchronous streaming
for chunk in chat.stream("Write me a 1 verse song about goldfish on the moon"):
    print(chunk.content, end="|", flush=True)

# Async streaming
async for chunk in chat.astream("Write me a 1 verse song about goldfish on the moon"):
    print(chunk.content, end="|", flush=True)

# Stream events for complex chains
idx = 0
async for event in chat.astream_events("Write me a 1 verse song about goldfish on the moon"):
    if event['event'] == 'on_chat_model_stream':
        chunk = event['data']['chunk']
        print(chunk.content, end="", flush=True)
```

## Tool Calling with Chat Models

Define tools and bind them to chat models for structured output generation.

```python
from pydantic import BaseModel, Field

# Define tools using Pydantic
class Add(BaseModel):
    """Add two integers."""
    a: int = Field(..., description="First integer")
    b: int = Field(..., description="Second integer")

class Multiply(BaseModel):
    """Multiply two integers."""
    a: int = Field(..., description="First integer")
    b: int = Field(..., description="Second integer")

# Bind tools to model
tools = [Add, Multiply]
model_with_tools = model.bind_tools(tools)

# Invoke model with tools
response = model_with_tools.invoke("What is 3 times 12?")

# Access tool calls
for tool_call in response.tool_calls:
    print(f"Tool: {tool_call['name']}")
    print(f"Arguments: {tool_call['args']}")

# Alternative: Define tools as Python functions
def add(a: int, b: int) -> int:
    """Add two integers.

    Args:
        a: First integer
        b: Second integer
    """
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two integers.

    Args:
        a: First integer
        b: Second integer
    """
    return a * b

model_with_tools = model.bind_tools([add, multiply])
```

## Building Chatbots with Memory

Create conversational chatbots with persistent message history using LangGraph.

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END

# Define the chatbot logic
def call_model(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": response}

# Build the graph
workflow = StateGraph(state_schema=MessagesState)
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)
workflow.add_edge("model", END)

# Add memory persistence
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# Use the chatbot with conversation history
config = {"configurable": {"thread_id": "abc123"}}

response = app.invoke(
    {"messages": [HumanMessage(content="Hi! I'm Bob")]},
    config=config
)
print(response["messages"][-1].content)

# Continue the conversation
response = app.invoke(
    {"messages": [HumanMessage(content="What's my name?")]},
    config=config
)
print(response["messages"][-1].content)  # Output: "Your name is Bob!"
```

## Retrieval Augmented Generation (RAG)

Build question-answering systems that retrieve relevant information from documents.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_community.document_loaders import WebBaseLoader

# Load documents
loader = WebBaseLoader("https://example.com/docs")
docs = loader.load()

# Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
splits = text_splitter.split_documents(docs)

# Create embeddings and vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vectorstore = InMemoryVectorStore.from_documents(splits, embeddings)

# Create retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# Build RAG chain
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template("""
Answer the question based on the following context:

Context: {context}

Question: {question}

Answer:
""")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Use the chain
question = "What is the main topic?"
docs = retriever.invoke(question)
context = format_docs(docs)

response = model.invoke(
    prompt.format_messages(context=context, question=question)
)
print(response.content)
```

## LangChain Expression Language (LCEL)

Chain components together using declarative syntax for optimized execution.

```python
from langchain_core.runnables import RunnableSequence, RunnableParallel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Create a simple chain
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
output_parser = StrOutputParser()

# Chain using pipe operator
chain = prompt | model | output_parser

# Invoke the chain
result = chain.invoke({"topic": "programming"})
print(result)

# Batch processing
results = chain.batch([
    {"topic": "cats"},
    {"topic": "dogs"},
    {"topic": "birds"}
])

# Streaming
for chunk in chain.stream({"topic": "space"}):
    print(chunk, end="", flush=True)

# Parallel execution
parallel_chain = RunnableParallel({
    "joke": prompt | model | output_parser,
    "poem": ChatPromptTemplate.from_template("Write a poem about {topic}") | model | output_parser
})

result = parallel_chain.invoke({"topic": "ocean"})
print(result)  # {"joke": "...", "poem": "..."}
```

## Document Loaders and Text Splitters

Load documents from various sources and split them into manageable chunks.

```python
# Load PDF documents
from langchain_community.document_loaders import PyPDFLoader

pdf_loader = PyPDFLoader("document.pdf")
pdf_docs = pdf_loader.load()

# Load CSV data
from langchain_community.document_loaders import CSVLoader

csv_loader = CSVLoader("data.csv")
csv_docs = csv_loader.load()

# Load web pages
from langchain_community.document_loaders import WebBaseLoader

web_loader = WebBaseLoader(["https://example.com/page1", "https://example.com/page2"])
web_docs = web_loader.load()

# Split by character
from langchain_text_splitters import CharacterTextSplitter

char_splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=1000,
    chunk_overlap=200
)
char_splits = char_splitter.split_documents(pdf_docs)

# Split code
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

python_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON,
    chunk_size=500,
    chunk_overlap=50
)

# Split by tokens
from langchain_text_splitters import TokenTextSplitter

token_splitter = TokenTextSplitter(chunk_size=100, chunk_overlap=20)
token_splits = token_splitter.split_documents(web_docs)
```

## Vector Stores and Embeddings

Store and retrieve document embeddings for semantic search.

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS

# Initialize embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

# Create Chroma vector store
chroma_store = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# Create FAISS vector store
faiss_store = FAISS.from_documents(
    documents=splits,
    embedding=embeddings
)

# Similarity search
results = chroma_store.similarity_search("What is LangChain?", k=3)
for doc in results:
    print(doc.page_content)

# Similarity search with scores
results_with_scores = chroma_store.similarity_search_with_score("What is LangChain?", k=3)
for doc, score in results_with_scores:
    print(f"Score: {score}")
    print(doc.page_content)

# Use as retriever
retriever = chroma_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}
)

docs = retriever.invoke("Tell me about agents")
```

## Custom Retriever with Reranking

Implement advanced retrieval strategies with contextual compression and reranking.

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

# Base retriever
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# Create reranker
cross_encoder = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
reranker = CrossEncoderReranker(model=cross_encoder, top_n=3)

# Compression retriever
compression_retriever = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=base_retriever
)

# Use the retriever
compressed_docs = compression_retriever.invoke("What are the key features?")
for doc in compressed_docs:
    print(doc.page_content)

# Multi-query retriever
from langchain.retrievers.multi_query import MultiQueryRetriever

multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=model
)

# Generates multiple queries and retrieves for each
docs = multi_query_retriever.invoke("Tell me about the framework")
```

## Output Parsers and Structured Output

Parse LLM responses into structured formats for downstream processing.

```python
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field

# String output parser
str_parser = StrOutputParser()
chain = prompt | model | str_parser
result = chain.invoke({"topic": "AI"})  # Returns string

# JSON output parser
json_parser = JsonOutputParser()
prompt_json = ChatPromptTemplate.from_template(
    "Extract information as JSON: {query}\n{format_instructions}"
)
chain_json = prompt_json | model | json_parser

result = chain_json.invoke({
    "query": "Tell me about John, age 30, from New York",
    "format_instructions": json_parser.get_format_instructions()
})
print(result)  # {"name": "John", "age": 30, "city": "New York"}

# Pydantic output parser
class Person(BaseModel):
    name: str = Field(description="Person's name")
    age: int = Field(description="Person's age")
    city: str = Field(description="City of residence")

pydantic_parser = PydanticOutputParser(pydantic_object=Person)
prompt_pydantic = ChatPromptTemplate.from_template(
    "Extract information: {query}\n{format_instructions}"
)

chain_pydantic = prompt_pydantic | model | pydantic_parser
result = chain_pydantic.invoke({
    "query": "John is 30 years old and lives in New York",
    "format_instructions": pydantic_parser.get_format_instructions()
})
print(result.name, result.age, result.city)  # Pydantic object

# Structured output with bind
class Answer(BaseModel):
    answer: str = Field(description="The answer to the question")
    confidence: float = Field(description="Confidence score 0-1")

model_structured = model.with_structured_output(Answer)
result = model_structured.invoke("What is the capital of France?")
print(result.answer, result.confidence)
```

## Prompt Templates and Few-Shot Learning

Create reusable prompt templates with dynamic variables and examples.

```python
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.prompts import PromptTemplate

# Basic prompt template
basic_prompt = ChatPromptTemplate.from_template(
    "Tell me a {adjective} story about {subject}"
)
messages = basic_prompt.format_messages(adjective="funny", subject="cats")

# Multi-message template
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that translates {input_language} to {output_language}."),
    ("human", "{text}")
])

messages = chat_prompt.format_messages(
    input_language="English",
    output_language="French",
    text="Hello, how are you?"
)

# Few-shot prompting
examples = [
    {"input": "2+2", "output": "4"},
    {"input": "3+3", "output": "6"},
    {"input": "5+5", "output": "10"}
]

example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{output}")
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples
)

final_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a calculator. Calculate the following."),
    few_shot_prompt,
    ("human", "{input}")
])

chain = final_prompt | model
result = chain.invoke({"input": "7+7"})
print(result.content)  # "14"

# Partial formatting
partial_prompt = basic_prompt.partial(adjective="exciting")
messages = partial_prompt.format_messages(subject="space exploration")
```

## Agents and Tool Execution

Build agents that can reason and take actions using tools.

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool

# Define tools
@tool
def search_wikipedia(query: str) -> str:
    """Search Wikipedia for information about a topic."""
    # Implementation would use actual Wikipedia API
    return f"Wikipedia results for: {query}"

@tool
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    try:
        return eval(expression)
    except Exception as e:
        return f"Error: {e}"

@tool
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    return f"Weather in {location}: Sunny, 72°F"

tools = [search_wikipedia, calculate, get_weather]

# Create agent prompt
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Use tools when needed."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# Create agent
agent = create_tool_calling_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Execute agent
result = agent_executor.invoke({
    "input": "What's 15 multiplied by 23, and what's the weather in Paris?"
})
print(result["output"])

# Agent with memory
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
agent_with_memory = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True
)

result = agent_with_memory.invoke({"input": "Hello, I'm Alice"})
result = agent_with_memory.invoke({"input": "What's my name?"})
```

## LangServe Deployment

Deploy LangChain runnables as REST APIs using FastAPI.

```python
# server.py
from fastapi import FastAPI
from langserve import add_routes
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple API server using LangChain's Runnable interfaces"
)

# Create a simple chain
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
model = ChatOpenAI(model="gpt-4")
chain = prompt | model

# Add routes
add_routes(
    app,
    chain,
    path="/joke",
)

# Run with: uvicorn server:app --host 0.0.0.0 --port 8000

# Client usage
from langserve import RemoteRunnable

# Connect to the deployed service
remote_chain = RemoteRunnable("http://localhost:8000/joke")

# Invoke the remote chain
result = remote_chain.invoke({"topic": "programming"})
print(result)

# Stream from remote
for chunk in remote_chain.stream({"topic": "cats"}):
    print(chunk.content, end="", flush=True)

# Batch requests
results = remote_chain.batch([
    {"topic": "dogs"},
    {"topic": "space"},
    {"topic": "science"}
])
```

## Callbacks and Tracing with LangSmith

Monitor and debug LangChain applications with callbacks and LangSmith integration.

```python
import os
from langchain.callbacks import StdOutCallbackHandler
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# Setup LangSmith
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "your-api-key"
os.environ["LANGSMITH_PROJECT"] = "my-project"

# Standard output callback
stdout_handler = StdOutCallbackHandler()
model_with_callback = model.with_config(callbacks=[stdout_handler])
response = model_with_callback.invoke("Tell me a joke")

# Streaming callback
streaming_handler = StreamingStdOutCallbackHandler()
model_streaming = model.with_config(callbacks=[streaming_handler])
response = model_streaming.invoke("Write a poem")

# Custom callback
from langchain.callbacks.base import BaseCallbackHandler

class CustomHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"LLM started with prompts: {prompts}")

    def on_llm_end(self, response, **kwargs):
        print(f"LLM finished with response: {response}")

    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"Tool started: {serialized['name']}")

    def on_tool_end(self, output, **kwargs):
        print(f"Tool finished with output: {output}")

custom_handler = CustomHandler()
chain_with_callback = chain.with_config(callbacks=[custom_handler])
result = chain_with_callback.invoke({"topic": "AI"})

# Runtime callbacks
result = chain.invoke(
    {"topic": "space"},
    config={"callbacks": [custom_handler]}
)
```

## Caching and Rate Limiting

Optimize performance and manage API costs with caching and rate limiting.

```python
from langchain.cache import InMemoryCache, SQLiteCache
from langchain.globals import set_llm_cache
import time

# In-memory cache
set_llm_cache(InMemoryCache())

# First call - hits API
start = time.time()
response1 = model.invoke("What is 2+2?")
print(f"First call: {time.time() - start:.2f}s")

# Second call - cached
start = time.time()
response2 = model.invoke("What is 2+2?")
print(f"Cached call: {time.time() - start:.2f}s")

# SQLite cache (persistent)
set_llm_cache(SQLiteCache(database_path=".langchain.db"))

# Rate limiting
from langchain_openai import ChatOpenAI

rate_limited_model = ChatOpenAI(
    model="gpt-4",
    max_retries=3,
    request_timeout=30,
    max_tokens=1000
)

# Custom rate limiter
from langchain_core.rate_limiters import InMemoryRateLimiter

rate_limiter = InMemoryRateLimiter(
    requests_per_second=1,
    check_every_n_seconds=0.1,
    max_bucket_size=10
)

model_with_limiter = ChatOpenAI(
    model="gpt-4",
    rate_limiter=rate_limiter
)

# Batch with rate limiting
requests = [f"Tell me about number {i}" for i in range(10)]
responses = model_with_limiter.batch(requests)  # Respects rate limit
```

## Summary

LangChain provides a comprehensive framework for building production-ready LLM applications with minimal boilerplate code. The framework's key strength lies in its standard interfaces that enable seamless integration with hundreds of providers while maintaining consistent APIs across different components. Whether building simple chatbots, complex retrieval systems, or autonomous agents, developers can leverage LangChain's modular architecture to compose sophisticated applications from well-tested building blocks.

Common use cases include conversational AI applications with memory and context management, retrieval-augmented generation systems for question-answering over custom knowledge bases, autonomous agents that can use tools to accomplish complex tasks, and document processing pipelines for ingestion and analysis. The framework's integration with LangSmith for tracing and debugging, LangServe for deployment, and LangGraph for complex orchestration makes it suitable for applications ranging from prototypes to production systems handling millions of requests. With built-in support for streaming, async operations, caching, and rate limiting, LangChain enables developers to build performant, scalable applications that harness the full power of large language models.