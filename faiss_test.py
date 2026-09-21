import faiss
import numpy as np


vectors = np.array([
    [1.0, 0.0],
    [0.0, 1.0],
    [0.8, 0.2]
], dtype="float32")  #3个二维向量


dimension = vectors.shape[1]   #此时.shape会返回（3,2）表示3个二维向量 [1]就是2

index = faiss.IndexFlatL2(
    dimension
)  #创建faiss索引，此处使用L2欧式距离判断相似度

index.add(
    vectors
)

query = np.array([
    [0.9, 0.1]
], dtype="float32") #question向量


distances, indices = index.search(
    query,
    2  #top_k=2
)

print("distances:")
print(distances)

print("indices:")
print(indices)