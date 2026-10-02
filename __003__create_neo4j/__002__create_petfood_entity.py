
import json

from common.neo4j_client import neo4j_client


def clean_text(value):
    if not value or str(value).strip() in ["", "\"\""]:
        return ""
    return str(value).strip()


def generate_petfood_queries(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        foods = json.load(f)

    queries = []
    food_names = set()
    food_alias_map = {}

    # 第一轮：创建节点和一方关系
    for food in foods:
        name = clean_text(food.get("名称"))
        if not name:
            continue

        alias = clean_text(food.get("别名"))
        brand = clean_text(food.get("品牌"))
        origin = clean_text(food.get("产地"))
        main_ingredient = clean_text(food.get("主要成分"))
        suitable_pet = clean_text(food.get("适用宠物"))
        processing = clean_text(food.get("加工工艺"))
        traits = clean_text(food.get("性状"))
        effect = clean_text(food.get("功效"))
        indication = clean_text(food.get("适用症状"))
        feeding = clean_text(food.get("喂食建议"))
        taboo = clean_text(food.get("禁忌"))
        effect_category = clean_text(food.get("功效分类"))
        food_category = clean_text(food.get("食品分类"))

        food_names.add(name)
        food_alias_map[name] = [clean_text(a) for a in alias.split("、") if clean_text(a) and clean_text(a) != name]

        queries.append((
            "MERGE (f:PetFood {name: $name}) "
            "SET f.alias=$alias, f.brand=$brand, f.origin=$origin, f.main_ingredient=$main_ingredient, "
            "f.suitable_pet=$suitable_pet, f.processing=$processing, f.traits=$traits, f.effect=$effect, "
            "f.indication=$indication, f.feeding=$feeding, f.taboo=$taboo, "
            "f.effect_category=$effect_category, f.food_category=$food_category, f.project='PET'",
            {
                "name": name, "alias": alias, "brand": brand, "origin": origin,
                "main_ingredient": main_ingredient, "suitable_pet": suitable_pet,
                "processing": processing, "traits": traits, "effect": effect,
                "indication": indication, "feeding": feeding, "taboo": taboo,
                "effect_category": effect_category, "food_category": food_category
            }
        ))

        if effect_category:
            queries.append((
                "MERGE (ec:EffectCategory {name: $name}) SET ec.project='PET'",
                {"name": effect_category}
            ))

        if food_category:
            queries.append((
                "MERGE (fc:PetFoodCategory {name: $name}) SET fc.project='PET'",
                {"name": food_category}
            ))

        if effect_category:
            queries.append((
                "MATCH (f:PetFood {name: $f_name}), (ec:EffectCategory {name: $ec_name}) "
                "MERGE (f)-[:BELONGS_TO_EFFECT_CATEGORY {project:'PET'}]->(ec)",
                {"f_name": name, "ec_name": effect_category}
            ))

        if effect_category and food_category:
            queries.append((
                "MATCH (ec:EffectCategory {name: $ec_name}), (fc:PetFoodCategory {name: $fc_name}) "
                "MERGE (ec)-[:BELONGS_TO_FOOD_CATEGORY {project:'PET'}]->(fc)",
                {"ec_name": effect_category, "fc_name": food_category}
            ))

    # 第二轮：添加宠物食品之间的双向别名关系
    for name, aliases in food_alias_map.items():
        for alias in aliases:
            if alias in food_names:
                queries.append((
                    "MATCH (f1:PetFood {name: $name1}), (f2:PetFood {name: $name2}) "
                    "MERGE (f1)-[:ALIAS_OF {project:'PET'}]->(f2)",
                    {"name1": name, "name2": alias}
                ))
                queries.append((
                    "MATCH (f1:PetFood {name: $name1}), (f2:PetFood {name: $name2}) "
                    "MERGE (f2)-[:ALIAS_OF {project:'PET'}]->(f1)",
                    {"name1": name, "name2": alias}
                ))

    return queries


if __name__ == "__main__":
    json_path = "../__002__extract_entity_relation/宠物食品属性提取结果_temp.json"

    queries = generate_petfood_queries(json_path)

    neo4j_client.run_multiple_cypher(queries)

    print("✅ 宠物食品知识图谱已成功导入 Neo4j。")
