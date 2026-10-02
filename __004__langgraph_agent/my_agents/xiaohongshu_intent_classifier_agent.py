
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import Runnable

from __004__langgraph_agent.agent_state import AgentState
from common.llm import my_llm, get_top_k_history


class XiaohongshuIntentClassifierAgent(Runnable):
    def invoke(self, agent_state: AgentState, config: dict = None) -> AgentState:
        """判断用户是否有发布小红书内容的意图"""
        if agent_state.get("stream_mode") and "is_has_xhs_intent" in agent_state:
            return agent_state

        session_id = agent_state.get("session_id", "default")
        past_messages = get_top_k_history(session_id)
        messages = [
            SystemMessage(content=(
                "你是一个小红书意图识别助手，专门判断用户是否有在小红书平台发布内容的意图。\n"
                "具有发小红书意图的表达包括但不限于：\n"
                " - 想写小红书笔记\n"
                " - 想知道小红书的内容怎么写\n"
                " - 想发布种草内容\n"
                " - 提到小红书爆款、笔记、流量、标签、推荐算法等\n"
                "没有发小红书意图的表达包括：\n"
                " - 没有提到任何和小红书相关的内容\n"
                " - 只是表达情绪或闲聊、提问其他平台内容（如知乎、微博、抖音）等\n"
                "请你判断用户是否有发小红书的意图。你只需要回答：是 或 否。不要补充其他内容。"
            ))] + past_messages + [
            HumanMessage(content=agent_state['input'])
        ]

        response = my_llm.invoke(messages).content.strip()
        agent_state['is_has_xhs_intent'] = "是" in response
        print(agent_state)
        return agent_state
