
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


class IngredientItem(BaseModel):
    food: str = Field(..., description="食材或食品名称")
    amount: Optional[str] = Field(None, description="食材用量，如 '50克'；如果未提供，则为 None")


class DiseaseSymptomRelation(BaseModel):
    disease: str = Field(..., description="疾病名称")
    symptoms: List[str] = Field(..., description="与该疾病明确相关的症状列表")


class RecipeResult(BaseModel):
    name: str = Field(..., description="宠物食谱的名称")
    effects: List[str] = Field(..., description="食谱的功效，用字符串列表表示")
    indications: List[IndicationItem] = Field(..., description="适用场景内容，标注出每一项是疾病还是症状")
    ingredients: List[IngredientItem] = Field(..., description="组成食材及其用量")
    relations: Optional[List[DiseaseSymptomRelation]] = Field(
        default=None,
        description="疾病与症状之间的明确对应关系；如果未明确说明可省略"
    )


class RecipeBatch(BaseModel):
    root: List[RecipeResult] = Field(..., description="一个食谱列表，每个为结构化的结果")


parser = PydanticOutputParser(pydantic_object=RecipeBatch)
format_instructions = parser.get_format_instructions()


def build_structured_prompt(recipe_list: List[dict]) -> PromptTemplate:
    prompt_str = "你是资深宠物营养与食谱专家，请对以下宠物食谱进行功效与适用场景的标签化处理：\n\n"
    for idx, f in enumerate(recipe_list, 1):
        prompt_str += (
            f"食谱{idx}：\n"
            f"名称：{f.get('名称', '')}\n"
            f"组成：{f.get('组成', '')}\n"
            f"功效：{f.get('功效', '')}\n"
            f"适用症状：{f.get('适用症状', '')}\n\n"
        )
    prompt_str += "请严格按照以下格式返回结果，是一个 JSON 数组：\n\n"
    prompt_str += "用以下JSON格式返回：\n{format_instructions}\n"

    return PromptTemplate(
        template=prompt_str,
        input_variables=[],
        partial_variables={"format_instructions": format_instructions}
    )


def process_batch(data: List[dict], output_path: str, batch_size: int = 5, resume: bool = True):
    existing_names = set()
    all_results = []

    if resume and os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                saved = json.load(f)
                for item in saved:
                    existing_names.add(item["name"])
                    all_results.append(RecipeResult(**item))
                print(f"🔁 已加载 {len(existing_names)} 个已处理食谱，跳过这些内容。")
            except Exception as e:
                print("⚠️ 读取已保存结果失败：", str(e))

    data_to_process = [item for item in data if item.get("名称") not in existing_names]

    for i in tqdm(range(0, len(data_to_process), batch_size), desc="处理中..."):
        batch = data_to_process[i: i + batch_size]
        prompt = build_structured_prompt(batch)
        chain = prompt | my_llm | parser

        try:
            response: RecipeBatch = chain.invoke({})
            results = response.root
            all_results.extend(results)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in all_results], f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"❌ 处理 batch {i // batch_size} 失败：{e}")
            continue

    return all_results


if __name__ == "__main__":
    INPUT_FILE = "食谱属性提取结果_temp.json"
    OUTPUT_FILE = "食谱实体关系细节提取结果.json"

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    processed = process_batch(
        data=raw_data,
        output_path=OUTPUT_FILE,
        batch_size=5,
        resume=True
    )

    print(f"✅ 处理完成，共处理 {len(processed)} 个食谱。结果保存在：{OUTPUT_FILE}")

