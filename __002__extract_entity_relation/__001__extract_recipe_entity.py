
import os
import pandas as pd
from langchain_core.messages import HumanMessage
from tqdm import tqdm
import json

from common.llm import my_llm

txt_folder_path = "../__001__crawler/宠物食谱"
excel_path = "../__001__crawler/宠物食谱列表.xlsx"
intermediate_path = "食谱属性提取结果_temp.json"
final_path = "食谱属性提取结果.xlsx"
start_from_scratch = False

expected_fields = [
    "名称", "别名", "出处", "组成", "功效",
    "适用症状", "做法", "禁忌", "功效分类", "食谱分类"
]


def parse_structured_output(text: str, expected_fields: list[str]) -> dict:
    result = {field: "" for field in expected_fields}
    lines = text.strip().splitlines()

    for line in lines:
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip().replace(" ", ""), v.strip()
        for field in expected_fields:
            if k == field.replace(" ", ""):
                result[field] = v
                break

    missing_fields = [f for f in expected_fields if result[f] == ""]
    if len(missing_fields) > len(expected_fields) // 2:
        raise ValueError(f"字段缺失过多（共{len(missing_fields)}项）: {missing_fields}")
    return result


excel_df = pd.read_excel(excel_path)
results = []
processed_names = set()

if not start_from_scratch and os.path.exists(intermediate_path):
    with open(intermediate_path, "r", encoding="utf-8") as f:
        results = json.load(f)
        processed_names = set(item["名称"] for item in results)

for _, row in tqdm(excel_df.iterrows(), total=len(excel_df)):
    name = row["食谱名称"]
    effect_class = row["功效分类"]
    recipe_class = row["食谱大类"]

    if name in processed_names:
        continue

    txt_path = os.path.join(txt_folder_path, f"{name}.txt")
    if not os.path.exists(txt_path):
        print(f"⚠️ 未找到文件：{txt_path}")
        continue

    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    prompt = f"""
你是一位宠物营养与食谱知识专家，请从下列宠物食谱资料中提取固定结构的字段内容。

食谱名称：{name}
资料内容如下（请严格依照原文提取）：

```
{content}
```

请严格按照如下格式输出结果，字段顺序不能更改，字段名前后禁止添加任何解释或注释。

每一行格式为：字段名: 内容（若无内容请填 ""）

名称: 
别名: 
出处: 
组成: 
功效: 
适用症状: 
做法: 
禁忌: 
功效分类: {effect_class}
食谱分类: {recipe_class}
    """.strip()

    try:
        response = my_llm.invoke([HumanMessage(content=prompt)])
        output = response.content

        print(f"\n====== {name} 提取结果预览 ======\n{output}\n==========================\n")

        field_values = parse_structured_output(output, expected_fields)
        results.append(field_values)

        with open(intermediate_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"❌ {name} 提取失败：{e}")

result_df = pd.DataFrame(results)
result_df.to_excel(final_path, index=False)
print(f"✅ 提取完成，结果保存至 {final_path}")
