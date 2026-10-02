
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import Runnable

from __004__langgraph_agent.agent_state import AgentState
from common.llm import my_llm, get_top_k_history


class DirectLLMAnswerAgent(Runnable):
    def build_messages(self, agent_state: AgentState):
        session_id = agent_state.get("session_id", "default")
        past_messages = get_top_k_history(session_id)

        return [SystemMessage(content=(
            "你是一个博学而通俗的宠物养护助手，擅长用简洁易懂的语言回答各种宠物相关问题。"
            "用户提问的问题，可能在宠物领域，也可能不在宠物领域。"
            "如果用户的问题超出宠物领域，也请尽可能给出有参考价值的自然语言解释。"
            "回答要自然、准确、简明扼要。"
        ))] + past_messages + [HumanMessage(content=agent_state['input'])]

    def invoke(self, agent_state: AgentState, config: dict = None) -> AgentState:
        """直接用大模型回答用户问题，不依赖图谱"""
        messages = self.build_messages(agent_state)

        if agent_state.get("stream_mode"):
            if agent_state.get("is_pet_question"):
                response = my_llm.invoke(messages).content.strip()
                agent_state['llm_direct_answer'] = response
                agent_state['output'] = ""
            else:
                agent_state['direct_messages'] = messages
                agent_state['llm_direct_answer'] = ""
                agent_state['output'] = ""
            if not agent_state.get('cypher_answer', None):
                agent_state['cypher_answer'] = ''
            return agent_state

        response = my_llm.invoke(messages).content.strip()
        agent_state['llm_direct_answer'] = response
        agent_state['output'] = response
        if not agent_state.get('cypher_answer', None):
            agent_state['cypher_answer'] = ''
        print(agent_state)
        return agent_state
