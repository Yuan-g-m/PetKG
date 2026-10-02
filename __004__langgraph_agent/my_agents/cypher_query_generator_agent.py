
from langchain_core.runnables import Runnable
from langchain_core.messages import SystemMessage, HumanMessage
import json

from __004__langgraph_agent.agent_state import AgentState
from common.llm import my_llm
from common.neo4j_client import neo4j_client
from tools.path_utils import resolve_from_project_root

# 预加载 schema 和 Neo4j
with open(resolve_from_project_root("__004__langgraph_agent/pet_metadata.json"), "r", encoding="utf-8") as f:
    schema_str = f.read()

SYSTEM_PROMPT = """
你是一个宠物知识图谱查询专家，你能根据用户的问题，参考以下图数据库结构，生成一条合适的 Cypher 查询语句（使用 Cypher 语法），并给出简要的查询意图说明。
如果问题无法用图谱进行回答，那么就返回空字符串。
如果使用 UNION 合并多个 MATCH 查询，所有 RETURN 的字段名必须一致，建议统一为 name 或 result。
当回答作用类问题时，调理疾病，功效，缓解症状，都是其作用。
图谱节点和关系类型如下：
{schema}

请严格按照如下格式输出：
Cypher:
<cypher语句>

Explanation:
<语句用途说明>
"""

system_prompt = SYSTEM_PROMPT.format(schema=schema_str)


class CypherQueryGeneratorAgent(Runnable):

    def invoke(self, agent_state: AgentState, config: dict = None) -> AgentState:
        """融合上游识别结果，根据自然语言与实体信息生成 Cypher 查询并执行"""
        user_question = agent_state['input']

        matched_symptoms = [m['matched_entity'] for m in agent_state.get('symptom_or_disease_entity_match_results', [])]
        matched_effects = [m['matched_entity'] for m in agent_state.get('effect_entity_match_results', [])]

        context_lines = []
        if matched_symptoms:
            context_lines.append(f"用户提到的症状或疾病包括：{', '.join(matched_symptoms)}。")
        if matched_effects:
            context_lines.append(f"用户提到的功效包括：{', '.join(matched_effects)}。")
        entity_context = "\n".join(context_lines)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"{entity_context}\n\n原始问题：{user_question}")
        ]

        print("🧠 正在调用 LLM 生成 Cypher 查询...")
        response = my_llm.invoke(messages).content

        try:
            cypher = response.split("Cypher:")[1].split("Explanation:")[0].strip()
            explanation = response.split("Explanation:")[1].strip()
        except Exception as e:
            agent_state['cypher'] = ""
            agent_state['cypher_result'] = []
            agent_state['cypher_answer'] = "此问题不适合用图谱查询。"
            return agent_state

        print("✅ 生成 Cypher：", cypher)

        ok, msg = neo4j_client.check_cypher_syntax(cypher)
        if not ok:
            agent_state['cypher'] = cypher
            agent_state['cypher_result'] = []
            agent_state['cypher_answer'] = f"Cypher 查询语法错误：{msg}"
            return agent_state

        result = neo4j_client.run_cypher(cypher)
        print("🔍 执行 Cypher 查询结果：", result)
        agent_state['cypher'] = cypher
        agent_state['cypher_result'] = result

        summary_prompt = [
            SystemMessage(content="你是一个宠物养护知识专家，请将以下图谱查询结果总结为通俗自然语言："),
            HumanMessage(
                content=f"原问题：{user_question}\n\n查询结果：\n{json.dumps(result, ensure_ascii=False, indent=2)}")
        ]
        summary_response = my_llm.invoke(summary_prompt).content
        agent_state['cypher_answer'] = summary_response
        agent_state['output'] = summary_response
        print("📢 生成的 cypher_answer：", summary_response)
        print("🔚 AgentState:", agent_state)

        return agent_state
