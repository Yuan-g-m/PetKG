
import os
import requests

from typing import Optional
from langchain_core.runnables import Runnable

from __004__langgraph_agent.agent_state import AgentState
from volcengine.visual.VisualService import VisualService

from tools.path_utils import resolve_from_project_root
from common.config import Config

conf = Config()


def sanitize_title_for_filename(title: str, max_length: int = 10) -> str:
    """将标题字符串清洗成适合作为文件名的格式"""
    invalid_chars = {":", "：", "/", "\\", "?", "*", "<", ">", "|", "\"", "｜", "“", "”", "‘", "’", "·", "·", " "}
    sanitized = ''.join(ch for ch in title[:max_length] if ch not in invalid_chars)
    return sanitized + ".png"


def generate_jimeng_prompt(title: str, content: str) -> str:
    return (
        f"一幅围绕宠物养护主题创作的图像，画面展现与标题内容相关的场景，"
        f"构图中包含可爱的宠物（如猫、狗、兔等）与养护行为（如喂食、梳毛、洗澡、玩耍、健康检查等），"
        f"整体氛围温馨、有爱、治愈，色调自然柔和，背景可融入家庭或户外自然环境，"
        f"表达健康、陪伴与快乐的情绪。"
        f"图片内容主题为:{title}"
        f"图片中不能有任何文字。"
        f"整体画面和谐、美观，符合图片质量要求。"
        f"图片中包含与宠物养护主题相关的元素，如宠物食品、玩具、梳毛工具等。"
        f"文字与画面协调，不影响整体美感。允许画风自由表达，可现代、写实、插画、水彩或其他形式。"
    )


def download_image_from_url(url: str, output_path: str):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)
        print(f"图片已保存：{output_path}")
    except requests.exceptions.RequestException as e:
        print(f"下载失败：{e}")


def generate_image(prompt: str, output_path: str):
    visual_service = VisualService()
    visual_service.set_ak(conf.JIMENG_AK)
    visual_service.set_sk(conf.JIMENG_SK)

    form = {
        "req_key": "jimeng_high_aes_general_v21_L",
        "prompt": prompt,
        "return_url": True
    }

    resp = visual_service.cv_process(form)
    image_urls = resp.get('data', {}).get('image_urls', [])
    if image_urls:
        download_image_from_url(image_urls[0], output_path)
        return output_path
    else:
        raise RuntimeError("图像生成失败，无有效图片链接返回")


class XiaohongshuImageGeneratorAgent(Runnable):
    def invoke(self, agent_state: AgentState, config: Optional[dict] = None) -> AgentState:
        """根据标题和内容生成宠物养护风格的小红书配图"""
        title = agent_state.get('xiaohongshu_pet_post_title')
        content = agent_state.get('xiaohongshu_pet_post_content')
        if not (title and content):
            raise ValueError("缺少必要字段：pet_post_title 或 pet_post_content")

        prompt = generate_jimeng_prompt(title, content)
        os.makedirs('picture', exist_ok=True)
        file_name = sanitize_title_for_filename(title)
        output_path = os.path.join('picture', file_name)
        output_path = resolve_from_project_root(output_path)

        try:
            image_path = generate_image(prompt, output_path)
            agent_state['xiaohongshu_pet_post_image_path'] = image_path
            print(f"图片生成成功: {image_path}")
        except Exception as exc:
            print(f"图片生成失败: {exc}")
            agent_state['xiaohongshu_pet_post_image_path'] = ""
        return agent_state
