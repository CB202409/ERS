from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import bs4
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastapi import FastAPI
from typing import Union
from langchain_core.messages import AIMessage, HumanMessage
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.document_loaders import PyMuPDFLoader


# .env 로드
load_dotenv()

# llm 모델 로드
llm = ChatOpenAI(model="gpt-4o", temperature=0)


# 최저임금 URL

### 나무위키 파싱 ###
# loader = WebBaseLoader(
#     web_paths=("https://namu.wiki/w/갤럭시%20S%20시리즈",),
#     bs_kwargs=dict(parse_only=bs4.SoupStrainer(id="app")),
# )

### XML 파싱(최저임금법) ###
# loader = WebBaseLoader(
#     web_paths=("https://www.law.go.kr/DRF/lawService.do?OC={아이디기입}&target=law&MST=218303&type=XML&mobileYn=&efYd=20200526",),
# )

### PDF 파싱 ###
loader = PyMuPDFLoader("./gun.pdf")


docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
  chunk_size=1000, 
  chunk_overlap=200,
  separators=["\n\n", "\n", ".", "!", "?", ";", ",", " "]
  )
splits = text_splitter.split_documents(docs)
vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings(model="text-embedding-3-small"))
retriever = vectorstore.as_retriever()


### Contextualize question ###
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)


### Answer question ###
from datetime import datetime

system_prompt = (
    f"The current date is {datetime.now().strftime('%Y-%m-%d')}."
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise."
    "\n\n"
    "{context}"
)
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)


### Statefully manage chat history ###
store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)

# 히스토리 최대 개수 (사용자, AI 메시지 합친 개수)
MAX_HISTORY_LENGTH = 10

def trim_history(history: ChatMessageHistory):
    while len(history.messages) > MAX_HISTORY_LENGTH:
        history.messages.pop(0)




# FastAPI 설정
app = FastAPI()

# CORS configuration
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def main(query: Union[str, None] = None, session_id: str = "default"):
    history = get_session_history(session_id)
    
    response = conversational_rag_chain.invoke(
        {"input": query},
        config={
            "configurable": {"session_id": session_id}
        },
    )
    
    trim_history(history)
    
    for message in history.messages:
        if isinstance(message, AIMessage):
            prefix = "AI"
        elif isinstance(message, HumanMessage):
            prefix = "User"
        else:
            prefix = "Unknown"
        print(f"{prefix}: {message.content}\n")
    return {"result": response["answer"]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("rag:app", host="0.0.0.0", port=8000, reload=True)
