
import json
from tqdm import tqdm

from common.neo4j_client import neo4j_client


def clean_text(value):
    if not value or value.strip() == "\"\"":
        return ""
    return value.strip()


def load_recipes_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_cypher_queries(recipes):
    queries = []

    for item in tqdm(recipes, desc="生成宠物食谱实体"):
        name = clean_text(item.get("名称"))
        alias = clean_text(item.get("别名"))
        source = clean_text(item.get("出处"))
        ingredients = clean_text(item.get("组成"))
        effect = clean_text(item.get("功效"))
        indication = clean_text(item.get("适用症状"))
        usage = clean_text(item.get("做法"))
        taboo = clean_text(item.get("禁忌"))
        effect_category = clean_text(item.get("功效分类"))
        recipe_category = clean_text(item.get("食谱分类"))
        std_source = clean_text(item.get("出处标准化"))

        queries.append((
            "MERGE (r:PetRecipe {name: $name}) "
            "SET r.alias = $alias, r.source = $source, r.ingredients = $ingredients, "
            "r.effect = $effect, r.indication = $indication, r.usage = $usage, "
            "r.taboo = $taboo, r.effect_category = $effect_category, "
            "r.recipe_category = $recipe_category, r.std_source = $std_source, "
            "r.project = 'PET'",
            {
                "name": name,
                "alias": alias,
                "source": source,
                "ingredients": ingredients,
                "effect": effect,
                "indication": indication,
                "usage": usage,
                "taboo": taboo,
                "effect_category": effect_category,
                "recipe_category": recipe_category,
                "std_source": std_source
            }
        ))

        if effect_category:
            queries.append((
                "MERGE (ec:EffectCategory {name: $name}) SET ec.project = 'PET'",
                {"name": effect_category}
            ))

        if recipe_category:
            queries.append((
                "MERGE (rc:PetRecipeCategory {name: $name}) SET rc.project = 'PET'",
                {"name": recipe_category}
            ))

        if std_source:
            queries.append((
                "MERGE (s:Source {name: $name}) SET s.project = 'PET'",
                {"name": std_source}
            ))

        if effect_category:
            queries.append((
                "MATCH (r:PetRecipe {name: $r_name}), (ec:EffectCategory {name: $ec_name}) "
                "MERGE (r)-[:BELONGS_TO_EFFECT_CATEGORY {project: 'PET'}]->(ec)",
                {"r_name": name, "ec_name": effect_category}
            ))

        if effect_category and recipe_category:
            queries.append((
                "MATCH (ec:EffectCategory {name: $ec_name}), (rc:PetRecipeCategory {name: $rc_name}) "
                "MERGE (ec)-[:BELONGS_TO {project: 'PET'}]->(rc)",
                {"ec_name": effect_category, "rc_name": recipe_category}
            ))

        if std_source:
            queries.append((
                "MATCH (r:PetRecipe {name: $r_name}), (s:Source {name: $s_name}) "
                "MERGE (r)-[:FROM_SOURCE {project: 'PET'}]->(s)",
                {"r_name": name, "s_name": std_source}
            ))

    return queries


if __name__ == "__main__":
    json_path = "../__002__extract_entity_relation/食谱属性提取结果_temp.json"

    recipes = load_recipes_from_json(json_path)
    queries = generate_cypher_queries(recipes)

    neo4j_client.run_multiple_cypher(queries)

    print("✅ PET recipes successfully imported into Neo4j.")
