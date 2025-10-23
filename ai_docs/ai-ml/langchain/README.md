# LangChain Documentation

Source: /python.langchain.com/llmstxt
Fetched: 2025-10-23
Tokens: 5000

## Overview

LangChain is a framework for developing applications powered by large language models (LLMs). It simplifies the entire LLM application lifecycle with open-source components and third-party integrations.

---

### Installing LangChain and LangSmith Dependencies (Python)

Source: https://python.langchain.com/docs/how_to/example_selectors_langsmith/

This command installs the required Python packages for interacting with LangSmith and LangChain, including `langsmith`, `langchain-core`, `langchain`, `langchain-openai`, and `langchain-benchmarks`. The `-qU` flags ensure a quiet, upgrade installation.

```Python
%pip install -qU "langsmith>=0.1.101" "langchain-core>=0.2.34" langchain langchain-openai langchain-benchmarks
```

---

### Initializing FewShotPromptTemplate in LangChain (Python)

Source: https://python.langchain.com/docs/how_to/few_shot_examples/

This snippet demonstrates how to initialize and use `FewShotPromptTemplate` in LangChain. It takes a list of examples, an `example_prompt` formatter, a `suffix` for the main query, and `input_variables`. It then shows how to invoke the prompt with an input and print the resulting string, guiding the LLM with provided examples.

```Python
from langchain_core.prompts import FewShotPromptTemplate

prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    suffix="Question: {input}",
    input_variables=["input"],
)
print(
    prompt.invoke({"input": "Who was the father of Mary Ball Washington?"}).to_string()
)
```

---

### Installing LangChain with OpenAI Dependencies

Source: https://python.langchain.com/docs/how_to/message_history/

This command installs the LangChain library along with the necessary dependencies for integrating with OpenAI models. The `-qU` flags ensure a quiet and upgraded installation.

```bash
pip install -qU "langchain[openai]"
```

---

### Installing LangGraph for Agent Examples

Source: https://python.langchain.com/docs/how_to/chat_token_usage_tracking/

This command installs the `langgraph` library, which is a dependency for running the agent-based token usage tracking example. The `-qU` flags ensure a quiet and upgraded installation.

```Shell
%pip install -qU langgraph
```

---

### Example Output of Few-Shot Prompting in Python

Source: https://python.langchain.com/docs/tutorials/extraction/

This snippet shows the expected output from the few-shot prompting example. Based on the provided `user` and `assistant` message pairs, the LLM correctly infers the operation represented by '🦜' and applies it to the final input '3 🦜 4', resulting in '7'. This demonstrates the effectiveness of few-shot examples in guiding the model's reasoning.

```text
7
```

---

### Installing Core LangChain Dependencies

Source: https://python.langchain.com/docs/how_to/convert_runnable_to_tool/

This command installs the necessary Python packages: `langchain-core`, `langchain-openai`, and `langgraph`, which are required for running the examples and demonstrations in this guide. The `%%capture --no-stderr` magic command suppresses output in environments like Jupyter.

```Shell
%%capture --no-stderr%pip install -U langchain-core langchain-openai langgraph
```

---

### Installing LangChain Core and OpenAI Dependencies - Python

Source: https://python.langchain.com/docs/how_to/query_few_shot/

This command installs the `langchain-core` and `langchain-openai` Python packages. These libraries are fundamental for developing applications with LangChain, providing core functionalities and integration with OpenAI's language models, respectively.

```Python
# %pip install -qU langchain-core langchain-openai
```

---

### Initializing Multi-Agent System Query Example in Python

Source: https://python.langchain.com/docs/how_to/query_few_shot/

This snippet defines an example input for a multi-agent system query. It sets up a `question` string and a `Search` object with a main query and several sub-queries, then appends this structured example to a global `examples` list. This example will be used later for few-shot learning.

```Python
question = "How to build multi-agent system and stream intermediate steps from it"query = Search(    query="How to build multi-agent system and stream intermediate steps from it",    sub_queries=[        "How to build multi-agent system",        "How to stream intermediate steps from multi-agent system",        "How to stream intermediate steps",    ],)examples.append({"input": question, "tool_calls": [query]})
```

---

### Demonstrating Few-Shot Prompting with Chat Models in Python

Source: https://python.langchain.com/docs/tutorials/extraction/

This Python code illustrates few-shot prompting for a chat model using a sequence of user and assistant messages. It provides examples of an operation (represented by '🦜') to guide the model's behavior. The `llm.invoke` call sends these messages, and the `response.content` prints the model's inferred output based on the provided examples, demonstrating how to steer LLM behavior.

```python
messages = [
    {"role": "user", "content": "2 🦜 2"},
    {"role": "assistant", "content": "4"},
    {"role": "user", "content": "2 🦜 3"},
    {"role": "assistant", "content": "5"},
    {"role": "user", "content": "3 🦜 4"},
]
response = llm.invoke(messages)
print(response.content)
```

---

### Installing LangChain Dependencies with Pip

Source: https://python.langchain.com/docs/how_to/query_multiple_queries/

This snippet shows how to install core LangChain packages, including `langchain`, `langchain-community`, `langchain-openai`, and `langchain-chroma`, using the `pip` package manager. It's a prerequisite for running LangChain applications and may require a kernel restart.

```Shell
%pip install -qU langchain langchain-community langchain-openai langchain-chroma
```

---

### Installing Ollama and Invoking a Text LLM in Python

Source: https://python.langchain.com/docs/how_to/local_llms/

This snippet demonstrates how to install the `langchain_ollama` package and initialize an `OllamaLLM` instance. It then shows how to invoke the LLM with a text prompt to get a direct text-in/text-out response. The `llama3.1:8b` model is used as an example.

```Python
%pip install -qU langchain_ollama

from langchain_ollama import OllamaLLM
llm = OllamaLLM(model="llama3.1:8b")
llm.invoke("The first man on the moon was ...")
```

---

### Initializing LengthBasedExampleSelector and FewShotPromptTemplate in Python

Source: https://python.langchain.com/docs/how_to/example_selectors_length_based/

This snippet demonstrates how to set up a `LengthBasedExampleSelector` to dynamically select examples for a `FewShotPromptTemplate`. It defines a list of examples, a `PromptTemplate` to format them, and then configures the example selector with a `max_length` to control how many examples are included based on the input length. Finally, it creates a `FewShotPromptTemplate` using this example selector.

```Python
from langchain_core.example_selectors import LengthBasedExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

# Examples of a pretend task of creating antonyms.
examples = [
    {"input": "happy", "output": "sad"},
    {"input": "tall", "output": "short"},
    {"input": "energetic", "output": "lethargic"},
    {"input": "sunny", "output": "gloomy"},
    {"input": "windy", "output": "calm"},
]

example_prompt = PromptTemplate(
    input_variables=["input", "output"],
    template="Input: {input}\nOutput: {output}",
)

example_selector = LengthBasedExampleSelector(
    # The examples it has available to choose from.
    examples=examples,
    # The PromptTemplate being used to format the examples.
    example_prompt=example_prompt,
    # The maximum length that the formatted examples should be.
    # Length is measured by the get_text_length function below.
    max_length=25,
    # The function used to get the length of a string, which is used
    # to determine which examples to include. It is commented out because
    # it is provided as a default value if none is specified.
    # get_text_length: Callable[[str], int] = lambda x: len(re.split("\n| ", x)))

dynamic_prompt = FewShotPromptTemplate(
    # We provide an ExampleSelector instead of examples.
    example_selector=example_selector,
    example_prompt=example_prompt,
    prefix="Give the antonym of every input",
    suffix="Input: {adjective}\nOutput:",
    input_variables=["adjective"],
)
```

---

### Selecting Examples with SemanticSimilarityExampleSelector in Python

Source: https://python.langchain.com/docs/how_to/sql_prompting/

This code demonstrates how to use the previously initialized `example_selector` to retrieve semantically similar examples. It takes a dictionary with an 'input' key (the user's query) and returns a list of relevant examples from the `examples` dataset.

```Python
example_selector.select_examples({"input": "how many artists are there?"})
```

---

### Configuring Few-Shot Example Formatter with LangChain PromptTemplate (Python)

Source: https://python.langchain.com/docs/how_to/few_shot_examples/

This snippet initializes a `PromptTemplate` object to format few-shot examples into a structured string. It defines a template with placeholders for a 'question' and its corresponding 'answer', which will be used to present examples to the LLM.

```Python
from langchain_core.prompts import PromptTemplate
example_prompt = PromptTemplate.from_template("Question: {question}\n{answer}")
```

---

### Installing LangChain with Pip

Source: https://python.langchain.com/docs/tutorials/summarization/

This command installs the LangChain library using pip, the Python package installer. It is a prerequisite for running the examples and tutorials in this guide.

```Shell
pip install langchain
```

---

### Initializing Chroma Vectorstore with OpenAI Embeddings (Python)

Source: https://python.langchain.com/docs/how_to/query_multiple_queries/

This snippet demonstrates how to create a Chroma vector store from a list of texts using OpenAIEmbeddings for generating embeddings. It initializes the embedding model and then populates the vector store, finally configuring a retriever for later use.

```Python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
texts = ["Harrison worked at Kensho", "Ankush worked at Facebook"]
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_texts(
    texts,
    embeddings,
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
```

---

### Setting up Example Data and Prompt Template in LangChain (Python)

Source: https://python.langchain.com/docs/how_to/example_selectors_mmr/

This snippet imports necessary LangChain components for example selection and prompt creation. It defines a `PromptTemplate` for structuring input/output pairs and initializes a list of example antonyms to be used for few-shot prompting.

```Python
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import (
    MaxMarginalRelevanceExampleSelector,
    SemanticSimilarityExampleSelector,
)
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_openai import OpenAIEmbeddings

example_prompt = PromptTemplate(
    input_variables=["input", "output"],
    template="Input: {input}\nOutput: {output}",
)
# Examples of a pretend task of creating antonyms.
examples = [
    {"input": "happy", "output": "sad"},
    {"input": "tall", "output": "short"},
    {"input": "energetic", "output": "lethargic"},
    {"input": "sunny", "output": "gloomy"},
    {"input": "windy", "output": "calm"},
]
```

---

### Initializing LangChain vs LangGraph Query Example in Python

Source: https://python.langchain.com/docs/how_to/query_few_shot/

Similar to the previous snippet, this code defines another example for comparing LangChain agents and LangGraph. It creates a `question` and a `Search` object with relevant sub-queries, then adds this example to the `examples` list. These examples are crucial for training the model to generate better queries.

```Python
question = "LangChain agents vs LangGraph?"query = Search(    query="What's the difference between LangChain agents and LangGraph? How do you deploy them?",    sub_queries=[        "What are LangChain agents",        "What is LangGraph",        "How do you deploy LangChain agents",        "How do you deploy LangGraph",    ],)examples.append({"input": question, "tool_calls": [query]})
```

---

### Adding Examples for LangChain Prompt Tuning in Python

Source: https://python.langchain.com/docs/how_to/query_few_shot/

This snippet demonstrates how to prepare examples for tuning the LangChain prompt. It defines a `question` and its corresponding gold-standard `Search` output, including a primary query and relevant sub-queries. This example is then appended to an `examples` list, which can be used to improve the LLM's query generation accuracy.

```Python
examples = []

question = "What's chat langchain, is it a langchain template?"
query = Search(
    query="What is chat langchain and is it a langchain template?",
    sub_queries=["What is chat langchain", "What is a langchain template"],
)
examples.append({"input": question, "tool_calls": [query]})
```

---

### Installing LangChain OpenAI Integration

Source: https://python.langchain.com/docs/tutorials/extraction/

This shell command installs the `langchain` package with the `openai` extra, providing necessary dependencies for integrating LangChain with OpenAI models. The `-qU` flags ensure a quiet, upgraded installation.

```Shell
pip install -qU "langchain[openai]"
```

---

### Example Output of Query Analyzer in LangChain Python

Source: https://python.langchain.com/docs/how_to/query_few_shot/

This snippet displays an example of the structured output generated by the `query_analyzer_with_examples` chain when invoked. The output is a `Search` object, demonstrating how the model, guided by the few-shot examples, decomposes the original question into a main query and relevant sub-queries, along with other parameters like `publish_year`.

```Python
Search(query="What's the difference between web voyager and reflection agents? Do both use langgraph?", sub_queries=['What is web voyager', 'What are reflection agents', 'Do web voyager and reflection agents use langgraph?'], publish_year=None)
```

---

### Generating Chat Messages from Examples using tool_example_to_messages (Python)

Source: https://python.langchain.com/docs/tutorials/extraction/

This snippet demonstrates how to use `tool_example_to_messages` from `langchain_core.utils.function_calling` to create a list of chat messages from pairs of input text and desired Pydantic `Data` objects. It includes both positive and negative examples for extraction, preparing them for use as few-shot prompts for a chat model. This requires `langchain-core>=0.3.20`.

```Python
from langchain_core.utils.function_calling import tool_example_to_messages
examples = [
    (
        "The ocean is vast and blue. It's more than 20,000 feet deep.",
        Data(people=[]),
    ),
    (
        "Fiona traveled far from France to Spain.",
        Data(people=[Person(name="Fiona", height_in_meters=None, hair_color=None)]),
    ),
]
messages = []
for txt, tool_call in examples:
    if tool_call.people:
        # This final message is optional for some providers
        ai_response = "Detected people."
    else:
        ai_response = "Detected no people."
    messages.extend(tool_example_to_messages(txt, [tool_call], ai_response=ai_response))
```

---

### Installing LangChain with OpenAI Dependencies

Source: https://python.langchain.com/docs/how_to/extraction_examples/

This command installs the necessary Python packages for LangChain, specifically including the OpenAI integration, in a quiet and upgrade-safe manner. It's a prerequisite for using OpenAI models with LangChain's features.

```Bash
pip install -qU "langchain[openai]"
```

---

### Configuring Semantic Similarity Example Selector and Few-Shot Prompt (Python)

Source: https://python.langchain.com/docs/how_to/example_selectors_similarity/

This code initializes the `SemanticSimilarityExampleSelector` using the previously defined examples, `OpenAIEmbeddings` for similarity calculations, and `Chroma` as the vector store. It then constructs a `FewShotPromptTemplate` that leverages this selector to dynamically insert the most semantically similar examples into the prompt based on the input.

```Python
example_selector = SemanticSimilarityExampleSelector.from_examples(
    # The list of examples available to select from.
    examples,
    # The embedding class used to produce embeddings which are used to measure semantic similarity.
    OpenAIEmbeddings(),
    # The VectorStore class that is used to store the embeddings and do a similarity search over.
    Chroma,
    # The number of examples to produce.
    k=1,
)
similar_prompt = FewShotPromptTemplate(
    # We provide an ExampleSelector instead of examples.
    example_selector=example_selector,
    example_prompt=example_prompt,
    prefix="Give the antonym of every input",
    suffix="Input: {adjective}\nOutput:",
    input_variables=["adjective"],
)
```

---

### Testing Few-Shot Prompt Formatting with LangChain (Python)

Source: https://python.langchain.com/docs/how_to/few_shot_examples/

This snippet demonstrates how to test the `example_prompt` by invoking it with the first example from the `examples` list. It then prints the formatted string, showing how a single few-shot example would be presented to the LLM.

```Python
print(example_prompt.invoke(examples[0]).to_string())
```

---

### Initializing PromptTemplate and Example Data (Python)

Source: https://python.langchain.com/docs/how_to/example_selectors_ngram/

This snippet imports necessary classes from LangChain and defines a PromptTemplate for formatting examples. It also initializes a list of example translation pairs that will be used by the example selector.

```Python
from langchain_community.example_selectors import NGramOverlapExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

example_prompt = PromptTemplate(
    input_variables=["input", "output"],
    template="Input: {input}\nOutput: {output}",
)

# Examples of a fictional translation task.
examples = [
    {"input": "See Spot run.", "output": "Ver correr a Spot."},
    {"input": "My dog barks.", "output": "Mi perro ladra."},
    {"input": "Spot can run.", "output": "Spot puede correr."},
]
```

---

### Adding New Examples to LengthBasedExampleSelector in Python

Source: https://python.langchain.com/docs/how_to/example_selectors_length_based/

This snippet demonstrates how to dynamically add a new example to an existing `LengthBasedExampleSelector` instance. After adding the new example, subsequent calls to format the `FewShotPromptTemplate` will consider this newly added example for inclusion, showcasing the flexibility of updating the example set at runtime.

```Python
# You can add an example to an example selector as well.new_example = {"input": "big", "output": "small"}
dynamic_prompt.example_selector.add_example(new_example)
print(dynamic_prompt.format(adjective="enthusiastic"))
```

---

### Defining Prompt Template and Examples for Antonym Generation (Python)

Source: https://python.langchain.com/docs/how_to/example_selectors_similarity/

This snippet imports necessary LangChain components, defines a basic `PromptTemplate` for input/output pairs, and initializes a list of example antonyms. These examples serve as the dataset from which the `SemanticSimilarityExampleSelector` will later choose the most relevant ones.

```Python
from langchain_chroma import Chroma
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_openai import OpenAIEmbeddings

example_prompt = PromptTemplate(
    input_variables=["input", "output"],
    template="Input: {input}\nOutput: {output}",
)

# Examples of a pretend task of creating antonyms.
examples = [
    {"input": "happy", "output": "sad"},
    {"input": "tall", "output": "short"},
    {"input": "energetic", "output": "lethargic"},
    {"input": "sunny", "output": "gloomy"},
    {"input": "windy", "output": "calm"},
]
```

---

### Installing LangChain Ollama Integration (Bash)

Source: https://python.langchain.com/docs/integrations/chat/ollama/

Installs the `langchain-ollama` package, which provides the necessary integration components for using Ollama models within the LangChain framework. This is the primary dependency for development.

```Bash
%pip install -qU langchain-ollama
```

---

### Initializing Vector Store for Semantic Similarity Example Selection - Python LangChain

Source: https://python.langchain.com/docs/how_to/few_shot_examples_chat/

This snippet imports necessary components for semantic similarity-based example selection. It defines a list of examples, prepares them for vectorization by joining input and output values, initializes OpenAIEmbeddings, and then creates a Chroma vector store populated with these examples and their metadata. This sets up the data for dynamic few-shot prompting.

```Python
from langchain_chroma import Chroma
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings

examples = [
    {"input": "2 🦜 2", "output": "4"},
    {"input": "2 🦜 3", "output": "5"},
    {"input": "2 🦜 4", "output": "6"},
    {"input": "What did the cow say to the moon?", "output": "nothing at all"},
    {
        "input": "Write me a poem about the moon",
        "output": "One for the moon, and one for me, who are we to talk about the moon?",
    },
]

to_vectorize = [" ".join(example.values()) for example in examples]
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_texts(to_vectorize, embeddings, metadatas=examples)
```

---

### Installing LangChain with OpenAI Integration

Source: https://python.langchain.com/docs/how_to/streaming/

This command installs the LangChain library along with the necessary dependencies for integrating with OpenAI models. The `-qU` flags ensure a quiet and upgrade installation, preparing the environment for developing LLM applications.

```bash
pip install -qU "langchain[openai]"
```

---

### Installing LangChain OpenAI Integration (Bash)

Source: https://python.langchain.com/docs/how_to/structured_output/

This shell command installs the `langchain` library along with its `openai` integration, which is necessary to use OpenAI models within LangChain. The `-qU` flags ensure a quiet installation and upgrade of existing packages.

```Bash
pip install -qU "langchain[openai]"
```
