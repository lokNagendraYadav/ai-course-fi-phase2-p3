import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def main() -> None:
    load_dotenv()

    # 1. Define the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("user", "{question}")
    ])

    # 2. Connect to Google Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=os.environ["GEMINI_API_KEY"],
    )

    # 3. Build the chain
    chain = prompt | llm | StrOutputParser()

    # 4. Run it
    response = chain.invoke({"question": "What is LangChain in one sentence?"})
    print(response)


# Only run when executed directly — importing this module must have no side
# effects (e.g. during a Vercel build, where GEMINI_API_KEY isn't present).
if __name__ == "__main__":
    main()
