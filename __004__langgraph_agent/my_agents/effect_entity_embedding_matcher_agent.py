
from langchain_core.runnables import Runnable
import faiss
import pickle
import numpy as np

from __004__langgraph_agent.agent_state import AgentState
from common.embedding_model import embedding_model
from tools.path_utils import resolve_from_project_root

INDEX_PATH = resolve_from_project_root("__004__langgraph_agent/pet_effect_node_index.index")
RECORDS_PATH = resolve_from_project_root("__004__langgraph_agent/pet_effect_node_texts.pkl")

index = faiss.read_index(INDEX_PATH)
with open(RECORDS_PATH, "rb") as f:
    node_records = pickle.load(f)


def _to_float32(a):
    a = np.asarray(a)
    if a.dtype != np.float32:
        a = a.astype(np.float32)
    return a


def _distances_to_similarity(dists: np.ndarray, metric_type: int, assume_unit_norm: bool = True) -> np.ndarray:
    """将 FAISS 返回的距离转换为相似度（越大越相似）"""
    dists = np.asarray(dists)
    if metric_type == faiss.METRIC_INNER_PRODUCT:
        return dists
    elif metric_type == faiss.METRIC_L2:
        if assume_unit_norm:
            return 1.0 - dists / 2.0
        else:
            return -dists
    else:
        return -dists


class EffectEntityEmbeddingMatcherAgent(Runnable):
    threshold = 0.85
    top_k = 3

    def match_entities(self, entities: list[str], debug: bool = False) -> list[dict]:
        """对功效实体进行向量匹配，只返回相似度 ≥ 阈值的结果"""
        if not entities:
            return []

        if index.ntotal == 0:
            if debug:
                print("[DEBUG] Index is empty (ntotal=0).")
            return []

        embeddings = embedding_model.encode(entities, normalize_embeddings=True)
        embeddings = _to_float32(embeddings)

        distances, indices = index.search(embeddings, self.top_k)

        metric_type = getattr(index, "metric_type", faiss.METRIC_L2)
        sims = _distances_to_similarity(distances, metric_type, assume_unit_norm=True)

        match_results = []
        for e_idx, (entity, idxs, sim_row) in enumerate(zip(entities, indices, sims)):
            if debug:
                raw_d = distances[e_idx]
                dbg = [
                    {
                        "faiss_idx": int(i),
                        "raw_dist": float(rd),
                        "sim": float(sr),
                        "name": node_records[i][0] if i >= 0 else None
                    }
                    for i, rd, sr in zip(idxs, raw_d, sim_row)
                ]
                print(f"[DEBUG] entity='{entity}': top{self.top_k} raw={dbg}")

            for i, sim in zip(idxs, sim_row):
                if i < 0:
                    continue
                if sim >= self.threshold:
                    name, label = node_records[i]
                    match_results.append({
                        "input_entity": entity,
                        "matched_entity": name,
                        "type": label,
                        "similarity": float(sim)
                    })

        return match_results

    def invoke(self, agent_state: AgentState, config: dict = None) -> AgentState:
        entities = agent_state.get('effect_entities', [])
        match_results = self.match_entities(entities)
        agent_state['effect_entity_match_results'] = match_results
        print(f"功效匹配结果: {match_results}")
        return agent_state


if __name__ == '__main__':
    agent = EffectEntityEmbeddingMatcherAgent()
    print(agent.match_entities(["美毛"], debug=True))
