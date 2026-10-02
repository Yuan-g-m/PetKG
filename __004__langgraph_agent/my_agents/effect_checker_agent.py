
from typing import List
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable

from __004__langgraph_agent.agent_state import AgentState
from common.llm import my_llm, get_top_k_history


class EffectCheckOutput(BaseModel):
    is_effect_question: bool
    entities: List[str]


class EffectCheckerAgent(Runnable):
    def invoke(self, agent_state: AgentState, config: dict = None) -> AgentState:
        """判断用户输入是否涉及功效，并提取功效实体"""
        parser = PydanticOutputParser(pydantic_object=EffectCheckOutput)
        format_instructions = parser.get_format_instructions()

        session_id = agent_state.get("session_id", "default")
        past_messages = get_top_k_history(session_id)

        messages = [
                       SystemMessage(content=(
                           "你是一个宠物问句分析助手，任务有两部分：\n"
                           "1. 判断用户的问题是否涉及宠物食品/食谱“功效”（如美毛、护肠胃、增强免疫、补钙、去泪痕等）。只要问题涉及任何功效类表达，即算相关；否则为不相关。\n"
                           "2. 如果相关，请抽取其中所有功效关键词，返回一个功效列表。\n\n"
                           f"请严格按以下格式返回：\n{format_instructions}"
                       ))] + past_messages + [
                       HumanMessage(content=agent_state['input'])
                   ]

        raw_output = my_llm.invoke(messages).content.strip()
        try:
            parsed_output = parser.parse(raw_output)
        except Exception as exc:
            print("⚠️ 功效解析失败，已降级处理：", exc)
            parsed_output = EffectCheckOutput(is_effect_question=False, entities=[])

        agent_state['is_effect_question'] = parsed_output.is_effect_question
        agent_state['effect_entities'] = parsed_output.entities
        print(agent_state)
        return agent_state
