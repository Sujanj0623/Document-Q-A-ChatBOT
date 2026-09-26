import os
from dotenv import load_dotenv
import streamlit as st
from login import login_page,logout
load_dotenv()
st.set_page_config(page_title="Document Q&A AI",page_icon="📖",layout="wide")
if "logged_in" not in st.session_state:
    st.session_state.logged_in=False
if not st.session_state.logged_in:
    login_page()
    st.stop()
st.sidebar.success(f"👋Welcome,{st.session_state.username}")
logout()
#print("api key loaded:",bool(os.getenv("GOOGLE_API_KEY")))
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings,ChatGoogleGenerativeAI
##chroma ,FAISS,Inmemory(Vector data base)
from langchain_community.vectorstores import InMemoryVectorStore

from time import sleep
llm=ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

if "vector_db" not in st.session_state:
    st.session_state.vector_db = None

if "messages" not in st.session_state:
    st.session_state.messages = []

def document_process(path):
    ##document loading
    loader=PyPDFLoader(path)
    docs=loader.load()
        ##Splitting
    splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
    docs=splitter.split_documents(docs)
    ##embeddings and vector stors
    embeddings=GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")
    vector_db=InMemoryVectorStore.from_documents(documents=docs,embedding=embeddings)
    st.session_state.vector_db = vector_db
    st.session_state.document_uploaded = True

st.subheader("📑Document Q&A ChatBot-Ask Anything")
if"document_uploaded" not in st.session_state:
    st.session_state.document_uploaded=False
##Document upload
if not st.session_state.document_uploaded:
    file = st.file_uploader(label="Select your PDF File" , type="pdf")
    if file:
        with open("uploaded_document.pdf" , "wb") as f:
            f.write(file.getvalue())
        st.markdown("Document Uploaded Sucessfully😊")
        with st.spinner("Processing....🛞"):
            document_process("./uploaded_document.pdf")
        st.markdown("Document processed Successfully...😊")
        sleep(2)
        st.rerun()

if st.session_state.document_uploaded and st.session_state.vector_db:
    for oneMessage in st.session_state.messages:
        role=oneMessage["role"]
        content=oneMessage["content"]
        st.chat_message(role).markdown(content)
    query=st.chat_input("Ask Anything...🧐")
    if query:
        st.session_state.messages.append({"role":"user","content":query})
        st.chat_message("user").markdown(query)
        documents = st.session_state.vector_db.similarity_search(query,k=2)
        context = ""
        for doc in documents:
            context += doc.page_content + "\n\n"
        prompt = f"""You are a helpful assistant and you provide answers for user questions based on the provided context. context: {context} and question is:{query}"""
        result = llm.invoke(prompt)
        if isinstance(result.content,str):
            answer_text=result.content
        else:
            answer_text = "".join(
                block.get("text","")
                for block in result.content
                if isinstance(block,dict) and block.get("type")=="text"
            )
        st.session_state.messages.append({"role":"ai","content":answer_text})
        st.chat_message("ai").markdown(answer_text)
##chat ui
