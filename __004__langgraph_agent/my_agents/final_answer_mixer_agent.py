
from langchain_core.runnables import Runnable
from langchain_core.messages import SystemMessage, HumanMessage

from __004__langgraph_agent.agent_state import AgentState
from common.llm import my_llm, get_top_k_history


class FinalAnswerMixerAgent(Runnable):
    """融合图谱回答与LLM回答，利用LLM进行补充增强输出"""

    def build_messages(self, agent_state: AgentState):
        user_question = agent_state.get("input", "")
        cypher_answer = agent_state.get("cypher_answer", "")
        llm_direct_answer = agent_state.get("llm_direct_answer", "")

        system_prompt = """
        你是一个宠物养护问答专家，需要将两个来源的回答进行融合：

        - 回答 A 来自宠物知识图谱，通常更权威、准确、结构化；
        - 回答 B 来自大语言模型，可能更通俗、丰富。

        请遵循以下融合策略：

        1. **始终以 A 为主要答案来源，保留其原始结构与表述。**
        2. **仅当 B 内容能对 A 做出“明确补充”（如饲养建议、注意事项、通俗举例）时，可将补充信息适当加入，不得覆盖或替换 A。**
        3. **若 A 完全为空或内容极差（如仅回答“无法回答”），则退而使用 B 答案。**
        4. 最终答案应清晰自然、专业准确，突出图谱权威性，适当增强可读性。

        请直接输出整合后的最终回答，不要说明答案来源。
        """.strip()

        content = f"""用户提问：{user_question}

        回答 A（图谱结果）：
        {cypher_answer}
        
        回答 B（模型结果）：
        {llm_direct_answer}
        """

        session_id = agent_state.get("session_id", "default")
        past_messages = get_top_k_history(session_id)
        return ([
                        SystemMessage(content=system_prompt)] + past_messages + [
                        HumanMessage(content=content.strip())
                    ])

    def invoke(self, agent_state: AgentState, config: dict = None) -> AgentState:
        messages = self.build_messages(agent_state)

        if agent_state.get("stream_mode"):
            agent_state["final_messages"] = messages
            agent_state["output"] = ""
            return agent_state

        print("🤖 正在让 LLM 整合两个答案...")
        final_answer = my_llm.invoke(messages).content.strip()

        agent_state["output"] = final_answer
        print("✅ LLM 整合输出：", final_answer)
        return agent_state
