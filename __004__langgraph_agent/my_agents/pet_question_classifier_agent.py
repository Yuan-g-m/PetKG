
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import Runnable

from __004__langgraph_agent.agent_state import AgentState
from common.llm import my_llm, get_top_k_history


class PetQuestionClassifierAgent(Runnable):
    def invoke(self, agent_state: AgentState, config: dict = None) -> AgentState:
        """判断一个问题是否属于宠物领域相关问题"""
        session_id = agent_state.get("session_id", "default")
        past_messages = get_top_k_history(session_id)
        messages = [
                       SystemMessage(content=(
                           "你是一个宠物问题分类助手，专门判断用户的问题是否与宠物领域有关。"
                           "宠物问题包括但不限于：宠物食品、宠物食谱、宠物疾病、症状、功效、营养、品种、饲养等。"
                           "非宠物问题包括：人类健康、情感、生活常识、法律、娱乐等。"
                           "请你只回答：是 或 否。不要补充其他内容。"
                       ))] + past_messages + [
                       HumanMessage(content=agent_state['input'])
                   ]

        response = my_llm.invoke(messages).content.strip()
        agent_state['is_pet_question'] = "是" in response
        print(agent_state)
        return agent_state
