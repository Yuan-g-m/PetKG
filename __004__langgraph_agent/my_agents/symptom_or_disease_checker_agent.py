
from typing import List
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable

from __004__langgraph_agent.agent_state import AgentState
from common.llm import my_llm, get_top_k_history


class SymptomOrDiseaseCheckOutput(BaseModel):
    is_symptom_or_disease: bool
    entities: List[str]


class SymptomOrDiseaseCheckerAgent(Runnable):
    def invoke(self, agent_state: AgentState, config: dict = None) -> AgentState:
        """判断一个问题是否涉及症状或疾病，并提取相关实体"""
        parser = PydanticOutputParser(pydantic_object=SymptomOrDiseaseCheckOutput)
        format_instructions = parser.get_format_instructions()

        session_id = agent_state.get("session_id", "default")
        past_messages = get_top_k_history(session_id)
        messages = [
                       SystemMessage(content=(
                           "你是一个宠物问句分析助手，任务有两部分：\n"
                           "1. 判断用户的问题是否涉及宠物“症状”或“疾病”。只要包含任一症状（如掉毛、呕吐、腹泻、咳嗽）或疾病（如皮肤病、肠胃炎、猫瘟），就算相关；否则为不相关。\n"
                           "2. 如果相关，请抽取其中涉及的症状或疾病名称，并以列表形式输出。\n\n"
                           "请你严格按照以下格式返回结果：\n"
                           f"{format_instructions}"
                       ))] + past_messages + [
                       HumanMessage(content=agent_state['input'])
                   ]

        raw_output = my_llm.invoke(messages).content.strip()
        try:
            parsed_output = parser.parse(raw_output)
        except Exception as exc:
            print("⚠️ 症状/疾病解析失败，已降级处理：", exc)
            parsed_output = SymptomOrDiseaseCheckOutput(is_symptom_or_disease=False, entities=[])

        agent_state['is_symptom_or_disease'] = parsed_output.is_symptom_or_disease
        agent_state['symptom_or_disease_entities'] = parsed_output.entities
        print(agent_state)
        return agent_state
