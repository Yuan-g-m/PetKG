
from typing import TypedDict, List, Any


class AgentState(TypedDict):
    input: str
    user_id: str
    session_id: str
    # 是否有发小红书的意图
    is_has_xhs_intent: bool
    # 小红书相关文案内容
    xiaohongshu_pet_post_title: str
    xiaohongshu_pet_post_content: str
    xiaohongshu_pet_post_strategies: List[str]
    # 小红书图片路径
    xiaohongshu_pet_post_image_path: str
    # 是否是宠物领域问题
    is_pet_question: bool
    # 直接回答暂存
    llm_direct_answer: str
    # 是否是症状或者疾病
    is_symptom_or_disease: bool
    symptom_or_disease_entities: List[str]
    symptom_or_disease_entity_match_results: List[dict]
    # 是否是功效
    is_effect_question: bool
    effect_entities: List[str]
    effect_entity_match_results: List[dict]
    # cypher查询相关
    cypher: str
    cypher_result: List
    cypher_answer: str

    # 流式输出模式与待流式化的消息
    stream_mode: bool
    direct_messages: List[Any]
    final_messages: List[Any]

    output: str
