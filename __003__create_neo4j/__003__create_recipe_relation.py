
import json
from common.neo4j_client import neo4j_client


def clean_text(v):
    if not v or str(v).strip() in ["", "\"\""]:
        return ""
    return str(v).strip()


def generate_recipe_graph_queries(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    queries = []

    for recipe in recipes:
        name = clean_text(recipe.get("name"))
        effects = recipe.get("effects", [])
        indications = recipe.get("indications", [])
        ingredients = recipe.get("ingredients", [])
        relations = recipe.get("relations", [])

        queries.append((
            "MERGE (r:PetRecipe {name: $name}) SET r.project='PET'",
            {"name": name}
        ))

        for effect in effects:
            effect_clean = clean_text(effect)
            queries.append((
                "MERGE (e:Effect {name: $effect}) SET e.project='PET'",
                {"effect": effect_clean}
            ))
            queries.append((
                "MATCH (r:PetRecipe {name: $name}), (e:Effect {name: $effect}) "
                "MERGE (r)-[:HAS_EFFECT {project:'PET'}]->(e)",
                {"name": name, "effect": effect_clean}
            ))

        for item in ingredients:
            food = clean_text(item.get("food"))
            amount = clean_text(item.get("amount"))
            queries.append((
                "MERGE (f:PetFood {name: $food}) SET f.project='PET'",
                {"food": food}
            ))
            queries.append((
                "MATCH (r:PetRecipe {name: $name}), (f:PetFood {name: $food}) "
                "MERGE (r)-[rel:HAS_INGREDIENT {project:'PET'}]->(f) "
                "SET rel.amount = $amount",
                {"name": name, "food": food, "amount": amount}
            ))

        for item in indications:
            content = clean_text(item.get("content"))
            type_ = item.get("type")
            if type_ == "疾病":
                queries.append((
                    "MERGE (d:Disease {name: $name}) SET d.project='PET'",
                    {"name": content}
                ))
                queries.append((
                    "MATCH (r:PetRecipe {name: $r_name}), (d:Disease {name: $d_name}) "
                    "MERGE (r)-[:TREATS_DISEASE {project:'PET'}]->(d)",
                    {"r_name": name, "d_name": content}
                ))
            elif type_ == "症状":
                queries.append((
                    "MERGE (s:Symptom {name: $name}) SET s.project='PET'",
                    {"name": content}
                ))
                queries.append((
                    "MATCH (r:PetRecipe {name: $r_name}), (s:Symptom {name: $s_name}) "
                    "MERGE (r)-[:ALLEVIATES_SYMPTOM {project:'PET'}]->(s)",
                    {"r_name": name, "s_name": content}
                ))

        for rel in relations or []:
            disease = clean_text(rel.get("disease"))
            symptom_list = rel.get("symptoms", [])
            queries.append((
                "MERGE (d:Disease {name: $name}) SET d.project='PET'",
                {"name": disease}
            ))
            for sym in symptom_list:
                symptom_clean = clean_text(sym)
                queries.append((
                    "MERGE (s:Symptom {name: $name}) SET s.project='PET'",
                    {"name": symptom_clean}
                ))
                queries.append((
                    "MATCH (d:Disease {name: $d_name}), (s:Symptom {name: $s_name}) "
                    "MERGE (d)-[:HAS_SYMPTOM {project:'PET'}]->(s)",
                    {"d_name": disease, "s_name": symptom_clean}
                ))

    return queries


if __name__ == "__main__":
    json_path = "../__002__extract_entity_relation/食谱实体关系细节提取结果.json"

    queries = generate_recipe_graph_queries(json_path)

    neo4j_client.run_multiple_cypher(queries)

    print("✅ 宠物食谱图谱导入完成！")
