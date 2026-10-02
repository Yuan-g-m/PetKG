
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable

from __004__langgraph_agent.agent_state import AgentState
from common.llm import my_llm, get_top_k_history


class XiaohongshuPetPostOutput(BaseModel):
    title: str
    content: str


class XiaohongshuPetPostAgent(Runnable):
    def invoke(self, agent_state: AgentState, config: dict = None) -> AgentState:
        """根据用户输入生成宠物养护类的小红书文案（包括标题、内容）"""
        parser = PydanticOutputParser(pydantic_object=XiaohongshuPetPostOutput)
        format_instructions = parser.get_format_instructions()

        session_id = agent_state.get("session_id", "default")
        past_messages = get_top_k_history(session_id)
        messages = [
                       SystemMessage(content=(
                           "你是一个专门为小红书平台撰写宠物养护内容的文案助手。\n"
                           "请根据用户提供的主题或需求，生成一条适合小红书发布的宠物养护类内容，要求包含：\n"
                           "1. 吸引人的标题（title）：不超过19个中文字符，简短有吸引力\n"
                           "2. 内容正文，具有分享性和实用性，语气自然亲切，适合社交媒体（content）\n"
                           "请你严格按照以下格式返回结果：\n"
                           f"{format_instructions}"
                       ))] + past_messages + [
                       HumanMessage(content=agent_state['input'])
                   ]

        raw_output = my_llm.invoke(messages).content.strip()
        parsed_output = parser.parse(raw_output)

        agent_state['xiaohongshu_pet_post_title'] = parsed_output.title
        agent_state['xiaohongshu_pet_post_content'] = parsed_output.content
        print(agent_state)
        return agent_state
