
import json
import re


# 特殊处理规则（写死替换）
def fix_special_titles(title):
    special_cases = {
        '《犬猫营养百科》': '《犬猫营养百科》',
        '《宠物营养学》': '《宠物营养学》',
        '《自制宠物餐》': '《自制宠物餐》',
    }
    return special_cases.get(title, title)


# 提取标准书名字段（带书名号）
def extract_standard_title(raw_source):
    match = re.search(r'《[^《》]+》', raw_source)
    if match:
        raw_title = match.group()
        return fix_special_titles(raw_title)
    return None


# 主逻辑：添加“出处标准化”字段并存储
def standardize_and_save(json_path, output_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data:
        source = item.get("出处", "")
        std_title = extract_standard_title(source)
        item["出处标准化"] = std_title if std_title else ""

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    input_file = '食谱属性提取结果_temp.json'   # 输入文件
    output_file = '食谱属性提取结果_temp.json'   # 输出文件
    standardize_and_save(input_file, output_file)
    print(f"已生成标准化文件：{output_file}")
