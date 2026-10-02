
import os
from dotenv import load_dotenv

from tools.path_utils import resolve_from_project_root

load_dotenv(".env")
load_dotenv(resolve_from_project_root(".env"))


class Config:
    """PetKG 宠物知识图谱项目配置（LLM 复用 FinRAG 的 OpenAI 兼容配置）"""

    def __init__(self):
        # 大模型（沿用 FinRAG 的 DeepSeek/OpenAI 兼容配置）
        self.LLM_MODEL = os.getenv("LLM_MODEL")
        self.LLM_API_KEY = os.getenv("LLM_API_KEY")
        self.LLM_BASE_URL = os.getenv("LLM_BASE_URL")

        # Neo4j 图数据库
        self.NEO4J_URI = os.getenv("NEO4J_URI")
        self.NEO4J_USER = os.getenv("NEO4J_USER")
        self.NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

        # 嵌入模型路径
        self.EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH")

        # 即梦文生图（宠物配图生成）
        self.JIMENG_AK = os.getenv("JIMENG_AK")
        self.JIMENG_SK = os.getenv("JIMENG_SK")


if __name__ == "__main__":
    config = Config()
    print(config.LLM_BASE_URL)
    print(config.LLM_MODEL)
    print(config.NEO4J_URI)
