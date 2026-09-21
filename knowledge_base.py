import hashlib
import faiss
from docx import Document
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

class KnowledgeBase:
    def __init__(self):
        self.model=None
        self.chunks=None
        self.embeddings=None
        self.index=None

        self.question_titles = {
            "1. 安全指数",
            "2. 如此编码",
            "3. 瑞瑞木板",
            "4. 序列查询",
            "5. 邻域均值",
            "6. 相反数",
            "7. 稀疏向量",
            "8. 风险人群筛查",
            "9. 学生排队",
            "10. 消除类游戏",
            "11. 两数之和",
            "12. 有效的括号",
            "13. 买卖股票的最佳时机",
            "14. 爬楼梯",
            "15. 最大子数组和"
        }

    def load(self): #切片，并向量化
        if(
        self.model is not None
        and self.chunks is not None
        and self.embeddings is not None
        and self.index is not None
        ):
            return

        file_path = (
            Path(__file__).resolve().parent
            / "rag_text"
            / "程序设计实训完整报告.docx"
        )
        document = Document(file_path)

        texts = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                texts.append(text)

        self.chunks = self.split_text(texts)
        if not self.chunks:
            raise ValueError("知识库没有生成任何chunk")

        self.model = SentenceTransformer(
            "BAAI/bge-small-zh-v1.5",
            local_files_only=True
        )

        embedding_path = (
            Path(__file__).resolve().parent
            / "rag_text"
            / "embedding.npy"
        )

        hash_path=(
            Path(__file__).resolve().parent
            /"rag_text"
            /"embedding.hash"
        )
        current_hash=self.get_chunks_hash()#当前chunks的hash
        cache_valid=False

        if embedding_path.exists() and hash_path.exists():
            old_hash= hash_path.read_text(
                encoding="utf-8"
            ).strip()
            if old_hash==current_hash:
                self.embeddings=np.load(embedding_path)  
                cache_valid=True
                    
            else:
                self.embeddings=self.model.encode(self.chunks)    
                
                np.save(
                embedding_path,
                self.embeddings
            )

                hash_path.write_text(
                    current_hash,
                    encoding="utf-8"
                )

        else:
            self.embeddings = self.model.encode(
                self.chunks
            )

            np.save(
                embedding_path,
                self.embeddings
            )

            hash_path.write_text(
                current_hash,
                encoding="utf-8"
            )

        index_path=(Path(__file__).resolve().parent
                    /"rag_text"
                    /"faiss.index"
                    )

        self.embeddings=self.embeddings.astype("float32")
        if cache_valid and index_path.exists():
            print("从本地读取faiss索引")
            self.index=faiss.read_index(str(index_path))
        else:
            dimension=self.embeddings.shape[1]
            self.index=faiss.IndexFlatL2(dimension)
            self.index.add(self.embeddings)
            faiss.write_index(
                self.index,
                str(index_path)
            )

    def search_faiss(self,question:str,top_k=3):
        self.load()
        question_embedding=self.model.encode(question)
        question_embedding=np.array(
            [question_embedding],
            dtype="float32"
            )
        distances,indices=self.index.search(
            question_embedding,
            top_k
        )
        results=[]
        for distance,index in zip(distances[0],indices[0]):
                results.append(
                    {
                    "chunk_index":int(index),
                    "distance":float(distance),
                    "text":self.chunks[index]
                    }
                )

        return results
    
    def split_text(self,texts,chunk_size=500):
        chunks=[]
        current_length=0
        current_parts=[]
        current_title=None

        for text in texts:
            if text in self.question_titles:#遇到标题
                if current_parts:
                    chunk="\n".join(current_parts)
                    chunks.append(chunk)

                current_title=text
                current_parts=[text]
                current_length=len(text)
                continue
#达到最大切分长度时，将被切的上一块的标题加入下一块
            if current_parts and current_length+len(text)>=chunk_size:
                chunk="\n".join(current_parts)
                chunks.append(chunk)

                current_length=0
                current_parts=[]
                if current_title is not None:
                    current_parts.append(current_title)
                    current_length += len(current_title)

            current_parts.append(text)
            current_length+=len(text)

        if current_parts:
            chunk="\n".join(current_parts)
            chunks.append(chunk)
        return chunks

    def get_chunks_hash(self):#用hash判断缓存缓存是否要更新
        text = "\n".join(self.chunks)
        return hashlib.md5(
            text.encode("utf-8")
        ).hexdigest()
    
    # def search_cosine(self,question:str,top_k=3):
    #     self.load()
    #     question_embedding=self.model.encode(question)

    #     scores=[]
    #     for i,embedding in enumerate(self.embeddings):
    #         score=(
    #             np.dot(question_embedding,embedding)
    #         )/(
    #             np.linalg.norm(question_embedding)*np.linalg.norm(embedding)
    #         )
    #         scores.append(
    #             (i,score)
    #         )
    #     scores.sort(
    #         key=lambda x:x[1],
    #         reverse=True
    #     )
    #     results=[]
    #     for i,similarity in scores[:top_k]:
    #         results.append(
    #             {
    #                 "chunk_index":i,
    #                 "similarity":similarity,
    #                 "text":self.chunks[i]
    #             }
    #         )
    #     return results