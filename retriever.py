class Retriever:
    def __init__(self,knowledge_base,top_k=3):
        self.knowledge_base=knowledge_base
        self.top_k=top_k

    def retrieve(self,question:str):
        results=self.knowledge_base.search_faiss(
            question,
            top_k=self.top_k
        )
        document=[]
        for result in results:
            document.append(
                result["text"]
            )
        return document