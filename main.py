from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# 1. Define the prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("user", "{question}")
])

# 2. Connect to OpenAI
llm = ChatGroq(model="llama-3.1-8b-instant")

# 3. Build the chain
chain = prompt | llm | StrOutputParser()

# 4. Run it
response = chain.invoke({"question": "What is LangChain in one sentence?"})
print(response)