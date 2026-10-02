
import faiss
import pickle

from common.embedding_model import embedding_model
from common.neo4j_client import neo4j_client


def get_embedding(texts):
    return embedding_model.encode(texts, normalize_embeddings=True)


# 从图谱中提取所有症状和疾病
records = neo4j_client.get_all_disease_and_symptom_names()

texts = [f"{name}" for name, label in records]  # eg: Symptom:掉毛
embeddings = get_embedding(texts)

# 构建向量索引
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# 保存索引和映射
faiss.write_index(index, "pet_disease_symptom_node_index.index")
with open("pet_disease_symptom_node_texts.pkl", "wb") as f:
    pickle.dump(records, f)
