
from typing import List, Dict, Any

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from common.config import Config

conf = Config()

# 配置大模型（沿用 FinRAG 的 OpenAI 兼容接口）
my_llm = ChatOpenAI(
    api_key=conf.LLM_API_KEY,
    base_url=conf.LLM_BASE_URL,
    model=conf.LLM_MODEL
)

# 会话历史存储（生产环境建议换用 Redis，示例先用内存 dict）
store = {}


def get_session_history(session_id: str):
    """获取某个会话的聊天历史"""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


def set_session_history(session_id: str, messages: List[Dict[str, Any]]) -> None:
    """用外部传入的历史消息重建某个会话的内存历史。"""
    history = InMemoryChatMessageHistory()
    for message in messages or []:
        role = message.get("role")
        content = message.get("content")
        if not content:
            continue
        if role == "assistant":
            history.add_ai_message(content)
        else:
            history.add_user_message(content)
    store[session_id] = history


def get_top_k_history(session_id: str, k: int = 8) -> List[BaseMessage]:
    """获取某个会话的最近 k 条消息"""
    history = get_session_history(session_id)
    return history.messages[-k:] if history.messages else []
