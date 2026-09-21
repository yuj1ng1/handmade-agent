from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_core.runnables import (RunnableLambda,RunnablePassthrough)
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from dotenv import load_dotenv
import hashlib
import os

class LangChainRag:
    def __init__(self):
        base_path=Path(__file__).resolve().parent
        self.model_name="BAAI/bge-small-zh-v1.5"
        self.chat_model_name="deepseek-flash"

        self.file_path=(
            base_path
            /"rag_text"
            /"程序设计实训完整报告.docx"
        )

        self.vector_path=(
            base_path
            /"rag_text"
            /"langchain_faiss"
        )

        self.hash_path=(
            base_path
            /"rag_text"
            /"langchain_faiss.hash"
        )

        self.chunk_size=500
        self.overlap=100

        self.embeddings=None
        self.vector_store=None
        self.retriever=None
        self.chain=None

    def load(self):
        if self.vector_store is not None:
            return 
        self.embeddings=HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={
                "local_files_only":True
            }
        )
        current_hash=self.get_cache_hash()
        cache_valid=False

        if self.vector_path.exists() and self.hash_path.exists():
            old_hash=self.hash_path.read_text(
                encoding="utf-8"
            ).strip()
            if old_hash==current_hash:
                cache_valid=True
        if cache_valid:
            self.vector_store=FAISS.load_local(
                str(self.vector_path),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            return
        
        loader=Docx2txtLoader(self.file_path)
        documents=loader.load()
        text_splitter=RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap
        )
        chunks=text_splitter.split_documents(documents)

        self.vector_store=FAISS.from_documents(
            chunks,
            self.embeddings
        )
        self.vector_store.save_local(
            str(self.vector_path)
        )
        self.hash_path.write_text(
            current_hash,
            encoding="utf-8"
        )

    def build_chain(self):
        if self.retriever is None:
            self.build_retriever()

        prompt_template = PromptTemplate.from_template(
        """
        请只根据下面提供的资料回答问题。
        如果资料中没有足够信息，请明确说明。

        资料：
        {context}

        问题：
        {question}
        """
            )
        
        load_dotenv()
        model=ChatDeepSeek(
            model=self.chat_model_name,
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            temperature=0
        )

        self.chain=(
            {
                "context":
                    self.retriever|RunnableLambda(self.format_documents),
                "question":RunnablePassthrough()
            }
            |prompt_template
            |model
            |StrOutputParser()
        )
    
    def build_retriever(self):
        if self.vector_store is None:
            self.load()
        self.retriever=self.vector_store.as_retriever(
            search_kwargs={
                "k":2
            }
        )


    def retrieve(self,question):#返回rag检索结果
        if self.retriever is None:
            self.build_retriever()
        return self.retriever.invoke(question)

    def ask(self,question):#检索加llm生成输出
        if self.chain is None:
            self.build_chain()
        return self.chain.invoke(question)
    
    def get_cache_hash(self):
        file_bytes=self.file_path.read_bytes()

        config_text=(
            self.model_name
            +"\n"
            +str(self.chunk_size)
            +"\n"
            +str(self.overlap)
        )
        hasher=hashlib.md5()
        hasher.update(file_bytes.encode("utf-8"))
        hasher.update(config_text)
        return hasher.hexdigest()
    
    def format_documents(self,documents):
        context_parts=[]
        for document in documents:
            context_parts.append(
                document.page_content
            )
        return "\n\n".join(context_parts)
    