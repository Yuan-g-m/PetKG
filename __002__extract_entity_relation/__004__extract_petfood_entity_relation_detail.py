
import json
import os
from tqdm import tqdm
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

from common.llm import my_llm


class IndicationItem(BaseModel):
    content: str = Field(..., description="具体的适用场景内容，如具体的疾病名或症状名")
    type: Literal["疾病", "症状"] = Field(..., description="判断是疾病或症状，只能是这两个值之一")


class DiseaseSymptomRelation(BaseModel):
    disease: str = Field(..., description="疾病名称")
    symptoms: List[str] = Field(..., description="与该疾病明确相关的症状列表")


class PetFoodResult(BaseModel):
    name: str = Field(..., description="宠物食品的名称")
    effects: List[str] = Field(..., description="食品的功效，用字符串列表表示")
    indications: List[IndicationItem] = Field(..., description="适用场景内容，标注出每一项是疾病还是症状")
    relations: Optional[List[DiseaseSymptomRelation]] = Field(
        default=None,
        description="疾病与症状之间的对应关系（可选）"
    )
    pet_types: List[Literal["犬", "猫", "兔", "仓鼠", "鸟", "鱼", "爬宠"]] = Field(
        ..., description="适用宠物类型，仅允许这些值之一或多种或空：犬、猫、兔、仓鼠、鸟、鱼、爬宠"
    )
    nutrition_types: List[Literal["高蛋白", "低脂", "高钙", "高纤维", "益生菌", "维生素", "矿物质", "无谷"]] = Field(
        ..., description="营养特点，仅允许这些值之一或多种或空：高蛋白、低脂、高钙、高纤维、益生菌、维生素、矿物质、无谷"
    )
    life_stages: List[Literal["幼年期", "成年期", "老年期", "孕期", "全阶段"]] = Field(
        ..., description="适用生命阶段，仅允许这些值之一或多种或空：幼年期、成年期、老年期、孕期、全阶段"
    )


class PetFoodBatch(BaseModel):
    root: List[PetFoodResult] = Field(..., description="结构化提取后的宠物食品列表")


pydantic_parser = PydanticOutputParser(pydantic_object=PetFoodBatch)
parser = pydantic_parser

format_instructions = parser.get_format_instructions()


def build_petfood_prompt(food_list: List[dict]) -> PromptTemplate:
    prompt_str = ("你是资深宠物食品与营养专家，请对以下宠物食品信息进行结构化提取，包括：功效、适用场景（并区分疾病和症状）、疾病与症状的对应关系、"
                  "适用宠物类型、营养特点和适用生命阶段。"
                  "如果某字段缺失，也必须返回空或者空数组（[]），不要省略字段；"
                  "如果disease-symptom 关系没有symptoms字段，那么就不用展示这个关系\n\n")
    for idx, h in enumerate(food_list, 1):
        prompt_str += (
            f"宠物食品{idx}：\n"
            f"名称：{h.get('名称', '')}\n"
            f"功效：{h.get('功效', '')}\n"
            f"适用症状：{h.get('适用症状', '')}\n"
            f"适用宠物：{h.get('适用宠物', '')}\n"
            f"主要成分：{h.get('主要成分', '')}\n\n"
        )
    prompt_str += "请严格按照以下格式返回结果，是一个 JSON 数组：\n"
    prompt_str += f"\n格式要求如下：\n{{format_instructions}}\n"
    return PromptTemplate(
        template=prompt_str,
        input_variables=[],
        partial_variables={"format_instructions": format_instructions}
    )


def process_petfood_batch(data: List[dict], output_path: str, batch_size: int = 5, resume: bool = True):
    existing_names = set()
    all_results = []

    if resume and os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                saved = json.load(f)
                for item in saved:
                    existing_names.add(item["name"])
                    all_results.append(PetFoodResult(**item))
                print(f"🔁 已加载 {len(existing_names)} 个已处理宠物食品，跳过这些内容。")
            except Exception as e:
                print("⚠️ 读取已保存结果失败：", str(e))

    data_to_process = [item for item in data if item.get("名称") not in existing_names]

    for i in tqdm(range(0, len(data_to_process), batch_size), desc="处理宠物食品数据中..."):
        batch = data_to_process[i: i + batch_size]
        prompt = build_petfood_prompt(batch)
        chain = prompt | my_llm | parser

        try:
            response: PetFoodBatch = chain.invoke({})
            results = response.root
            all_results.extend(results)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in all_results], f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"❌ 处理 batch {i // batch_size} 失败：{e}")
            continue

    return all_results


if __name__ == "__main__":
    INPUT_FILE = "宠物食品属性提取结果_temp.json"
    OUTPUT_FILE = "宠物食品实体关系细节提取结果.json"

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    processed = process_petfood_batch(
        data=raw_data,
        output_path=OUTPUT_FILE,
        batch_size=5,
        resume=True
    )

    print(f"✅ 处理完成，共处理 {len(processed)} 个宠物食品。结果保存在：{OUTPUT_FILE}")


