from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.runnables import (RunnableLambda,RunnablePassthrough)
from langchain_core.output_parsers import StrOutputParser
from pathlib import Path
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os 
import hashlib

def format_documents(documents):
    context_parts=[]

    for document in documents:
        context_parts.append(
            document.page_content
        )
    return "\n\n".join(
        context_parts
    )

def get_chunks_hash(chunks,model_name):#获取chunks的哈希值
    texts=[]
    for chunk in chunks:
        texts.append(
            chunk.page_content
        )
    full_text="\n".join(texts)
    cache_text=(
        full_text
        +"\n"
        +model_name
    )

    return hashlib.md5(
        cache_text.encode("utf-8")
    ).hexdigest()

model_name="BAAI/bge-small-zh-v1.5"
embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs={
        "local_files_only":True
    }
)

file_path=(Path(__file__).resolve().parent#读取文件
           /"rag_text"
           /"程序设计实训完整报告.docx"
           )

loader=Docx2txtLoader(file_path)
documents=loader.load()

text_splitter=RecursiveCharacterTextSplitter(#文档切分
    chunk_size=500,
    chunk_overlap=100
)
chunks=text_splitter.split_documents(documents)

vector_path=(Path(__file__).resolve().parent
             /"rag_text"
             /"langchain_faiss"
             )

hash_path=(Path(__file__).resolve().parent
           /"rag_text"
           /"langchain_faiss.hash"
           )
current_hash=get_chunks_hash(chunks,model_name)
cache_valid=False

if vector_path.exists() and hash_path.exists():
    old_hash=hash_path.read_text(
        encoding="utf-8",
    ).strip()

    if old_hash==current_hash:
        cache_valid=True

if cache_valid:
    print("从本地读取langchain faiss")
    vector_store=FAISS.load_local(
        str(vector_path),
        embeddings,
        allow_dangerous_deserialization=True
    )
else:
    print("首次创建langchain faiss")
    vector_store=FAISS.from_documents(
        chunks,
        embeddings
    )
    vector_store.save_local(str(vector_path))
    hash_path.write_text(
        current_hash,
        encoding="utf-8"
    )

retriever = vector_store.as_retriever(
    search_kwargs={"k": 2}
)

question=""

prompt_template=PromptTemplate.from_template("""
请只根据下面提供的资料回答问题。
如果资料中没有足够信息，请明确说明。

资料：
{context}

问题：
{question}
""")

load_dotenv()
model = ChatDeepSeek(
    model="deepseek-flash",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0
)
rag_chain=(
    {
        "context":retriever | RunnableLambda(format_documents),
        "question":RunnablePassthrough()
    }
    |prompt_template
    |model    #此时输出的是AIMESSAGE=(content="kfc......")
    |StrOutputParser()#转成普通字符串
)

response=rag_chain.invoke(
    question
)
print(response)

