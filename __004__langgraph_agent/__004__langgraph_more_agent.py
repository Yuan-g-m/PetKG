
from langgraph.graph import StateGraph, END

from __004__langgraph_agent.my_agents.cypher_query_generator_agent import CypherQueryGeneratorAgent
from __004__langgraph_agent.my_agents.direct_llm_answer_agent import DirectLLMAnswerAgent
from __004__langgraph_agent.my_agents.effect_checker_agent import EffectCheckerAgent
from __004__langgraph_agent.my_agents.effect_entity_embedding_matcher_agent import EffectEntityEmbeddingMatcherAgent
from __004__langgraph_agent.my_agents.final_answer_mixer_agent import FinalAnswerMixerAgent
from __004__langgraph_agent.my_agents.symptom_or_disease_checker_agent import SymptomOrDiseaseCheckerAgent
from __004__langgraph_agent.my_agents.symptom_or_disease_entity_embedding_matcher_agent import \
    SymptomOrDiseaseEntityEmbeddingMatcherAgent
from __004__langgraph_agent.my_agents.pet_question_classifier_agent import PetQuestionClassifierAgent
from __004__langgraph_agent.my_agents.xiaohongshu_image_generator_agent import XiaohongshuImageGeneratorAgent
from __004__langgraph_agent.my_agents.xiaohongshu_intent_classifier_agent import XiaohongshuIntentClassifierAgent
from __004__langgraph_agent.my_agents.xiaohongshu_pet_post_output_agent import XiaohongshuPetPostAgent
from __004__langgraph_agent.agent_state import AgentState
from common.llm import get_session_history, my_llm

# 构建 LangGraph 状态图
graph = StateGraph(AgentState)
# 添加各个代理节点到状态图
graph.add_node(XiaohongshuIntentClassifierAgent.__name__, XiaohongshuIntentClassifierAgent())
graph.add_node(XiaohongshuPetPostAgent.__name__, XiaohongshuPetPostAgent())
graph.add_node(XiaohongshuImageGeneratorAgent.__name__, XiaohongshuImageGeneratorAgent())
graph.add_node(PetQuestionClassifierAgent.__name__, PetQuestionClassifierAgent())
graph.add_node(DirectLLMAnswerAgent.__name__, DirectLLMAnswerAgent())
graph.add_node(SymptomOrDiseaseCheckerAgent.__name__, SymptomOrDiseaseCheckerAgent())
graph.add_node(SymptomOrDiseaseEntityEmbeddingMatcherAgent.__name__, SymptomOrDiseaseEntityEmbeddingMatcherAgent())
graph.add_node(EffectCheckerAgent.__name__, EffectCheckerAgent())
graph.add_node(EffectEntityEmbeddingMatcherAgent.__name__, EffectEntityEmbeddingMatcherAgent())
graph.add_node(CypherQueryGeneratorAgent.__name__, CypherQueryGeneratorAgent())
graph.add_node(FinalAnswerMixerAgent.__name__, FinalAnswerMixerAgent())

# 设置进入图节点入口
graph.set_entry_point(XiaohongshuIntentClassifierAgent.__name__)


def xiaohongshu_intent_classifier_agent_routing_control(state_agent: AgentState):
    # 根据问题是否为小红书发布意图，决定下一步的代理节点
    if state_agent.get("is_has_xhs_intent"):
        return XiaohongshuPetPostAgent.__name__
    return PetQuestionClassifierAgent.__name__


graph.add_conditional_edges(
    XiaohongshuIntentClassifierAgent.__name__,
    xiaohongshu_intent_classifier_agent_routing_control,
)

# 小红书文案生成后进入配图生成
graph.add_edge(XiaohongshuPetPostAgent.__name__, XiaohongshuImageGeneratorAgent.__name__)
graph.add_edge(XiaohongshuImageGeneratorAgent.__name__, END)


def pet_question_classifier_agent_routing_control(state_agent: AgentState):
    # 根据问题是否为宠物问题，决定下一步的代理节点
    if state_agent['is_pet_question']:
        return SymptomOrDiseaseCheckerAgent.__name__
    else:
        return DirectLLMAnswerAgent.__name__


graph.add_conditional_edges(PetQuestionClassifierAgent.__name__, pet_question_classifier_agent_routing_control)


def symptom_disease_checker_agent_routing_control(state_agent: AgentState):
    # 根据是否存在症状或疾病实体，决定下一步的代理节点
    if state_agent['is_symptom_or_disease'] and state_agent['symptom_or_disease_entities']:
        return SymptomOrDiseaseEntityEmbeddingMatcherAgent.__name__
    else:
        return EffectCheckerAgent.__name__


graph.add_conditional_edges(SymptomOrDiseaseCheckerAgent.__name__, symptom_disease_checker_agent_routing_control)
# 添加无条件边
graph.add_edge(SymptomOrDiseaseEntityEmbeddingMatcherAgent.__name__, EffectCheckerAgent.__name__)


def effect_checker_agent_routing_control(state_agent: AgentState):
    # 根据问题是否为功效问题，决定下一步的代理节点
    if state_agent['is_effect_question'] and state_agent['effect_entities']:
        return EffectEntityEmbeddingMatcherAgent.__name__
    else:
        return CypherQueryGeneratorAgent.__name__


graph.add_conditional_edges(EffectCheckerAgent.__name__, effect_checker_agent_routing_control)
# 添加无条件边
graph.add_edge(EffectEntityEmbeddingMatcherAgent.__name__, CypherQueryGeneratorAgent.__name__)
graph.add_edge(CypherQueryGeneratorAgent.__name__, DirectLLMAnswerAgent.__name__)


def direct_answer_agent_routing_control(state_agent: AgentState):
    # 根据问题是否为宠物问题，决定是否直接结束
    if state_agent['is_pet_question']:
        return FinalAnswerMixerAgent.__name__
    else:
        return END


graph.add_conditional_edges(DirectLLMAnswerAgent.__name__, direct_answer_agent_routing_control)
# 添加无条件边
graph.add_edge(FinalAnswerMixerAgent.__name__, END)
# 编译状态图
app = graph.compile()


def call_langgraph_ai(user_id, session_id, user_content):
    # 调用编译后的状态图应用
    response = app.invoke(
        {
            "input": user_content,
            "user_id": user_id,
            "session_id": session_id,
            "stream_mode": True,
            "is_has_xhs_intent": False,
        }
    )
    response_output = response.get("output") or response.get("llm_direct_answer") or ""
    history = get_session_history(session_id)
    history.add_user_message(user_content)
    history.add_ai_message(response_output)
    return False, (response_output,)


def call_xiaohongshu_ai(user_id: str, session_id: str, user_content: str) -> dict:
    """显式生成小红书图文内容，返回标题、正文和配图路径。"""
    response = app.invoke(
        {
            "input": user_content,
            "user_id": user_id,
            "session_id": session_id,
            "stream_mode": True,
            "is_has_xhs_intent": True,
        }
    )
    title = response.get("xiaohongshu_pet_post_title") or ""
    content = response.get("xiaohongshu_pet_post_content") or ""
    image_path = response.get("xiaohongshu_pet_post_image_path") or ""

    history = get_session_history(session_id)
    history.add_user_message(user_content)
    history.add_ai_message(f"{title}\n{content}")
    return {"title": title, "content": content, "image_path": image_path}


def _chunk_text(chunk) -> str:
    """兼容不同模型返回的流式 chunk 结构。"""
    content = getattr(chunk, "content", "")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(item.get("text") or item.get("content") or "")
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content or "")


def stream_langgraph_ai(user_id, session_id, user_content):
    """流式执行知识图谱问答。

    内部先完成图谱检索、实体识别、直接回答准备等前置步骤，
    最后通过 my_llm.stream 逐 token 返回最终答案。
    """
    state = {
        "input": user_content,
        "user_id": user_id,
        "session_id": session_id,
        "stream_mode": True,
        "is_has_xhs_intent": False,
    }
    response = app.invoke(state)

    if response.get("is_pet_question"):
        messages = response.get("final_messages") or []
    else:
        messages = response.get("direct_messages") or []

    full_answer = ""
    for chunk in my_llm.stream(messages):
        token = _chunk_text(chunk)
        if not token:
            continue
        full_answer += token
        yield token

    history = get_session_history(session_id)
    history.add_user_message(user_content)
    history.add_ai_message(full_answer)


if __name__ == '__main__':
    call_langgraph_ai("user_001", "session_001", "狗狗掉毛吃什么好呢？")
