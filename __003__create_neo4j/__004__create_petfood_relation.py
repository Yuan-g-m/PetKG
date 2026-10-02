
import json

from common.neo4j_client import neo4j_client


def clean_text(val):
    if not val or str(val).strip() in ["", "\"\""]:
        return ""
    return str(val).strip()


def generate_petfood_graph_queries(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        foods = json.load(f)

    queries = []

    for food in foods:
        name = clean_text(food.get("name"))

        queries.append((
            "MERGE (f:PetFood {name: $name}) SET f.project='PET'",
            {"name": name}
        ))

        for effect in food.get("effects", []):
            effect_clean = clean_text(effect)
            queries.append((
                "MERGE (e:Effect {name: $name}) SET e.project='PET'",
                {"name": effect_clean}
            ))
            queries.append((
                "MATCH (f:PetFood {name: $food}), (e:Effect {name: $effect}) "
                "MERGE (f)-[:HAS_EFFECT {project:'PET'}]->(e)",
                {"food": name, "effect": effect_clean}
            ))

        for item in food.get("indications", []):
            content = clean_text(item.get("content"))
            type_ = item.get("type")

            if type_ == "疾病":
                queries.append((
                    "MERGE (d:Disease {name: $name}) SET d.project='PET'",
                    {"name": content}
                ))
                queries.append((
                    "MATCH (f:PetFood {name: $food}), (d:Disease {name: $disease}) "
                    "MERGE (f)-[:TREATS_DISEASE {project:'PET'}]->(d)",
                    {"food": name, "disease": content}
                ))
            elif type_ == "症状":
                queries.append((
                    "MERGE (s:Symptom {name: $name}) SET s.project='PET'",
                    {"name": content}
                ))
                queries.append((
                    "MATCH (f:PetFood {name: $food}), (s:Symptom {name: $symptom}) "
                    "MERGE (f)-[:ALLEVIATES_SYMPTOM {project:'PET'}]->(s)",
                    {"food": name, "symptom": content}
                ))

        for pet_type in food.get("pet_types", []):
            pet_type_clean = clean_text(pet_type)
            queries.append((
                "MERGE (p:PetType {name: $name}) SET p.project='PET'",
                {"name": pet_type_clean}
            ))
            queries.append((
                "MATCH (f:PetFood {name: $food}), (p:PetType {name: $pet_type}) "
                "MERGE (f)-[:SUITS_PET_TYPE {project:'PET'}]->(p)",
                {"food": name, "pet_type": pet_type_clean}
            ))

        for nutrition in food.get("nutrition_types", []):
            nutrition_clean = clean_text(nutrition)
            queries.append((
                "MERGE (n:NutritionType {name: $name}) SET n.project='PET'",
                {"name": nutrition_clean}
            ))
            queries.append((
                "MATCH (f:PetFood {name: $food}), (n:NutritionType {name: $nutrition}) "
                "MERGE (f)-[:HAS_NUTRITION {project:'PET'}]->(n)",
                {"food": name, "nutrition": nutrition_clean}
            ))

        for stage in food.get("life_stages", []):
            stage_clean = clean_text(stage)
            queries.append((
                "MERGE (l:LifeStage {name: $name}) SET l.project='PET'",
                {"name": stage_clean}
            ))
            queries.append((
                "MATCH (f:PetFood {name: $food}), (l:LifeStage {name: $stage}) "
                "MERGE (f)-[:SUITS_LIFE_STAGE {project:'PET'}]->(l)",
                {"food": name, "stage": stage_clean}
            ))

        for rel in food.get("relations") or []:
            disease = clean_text(rel.get("disease"))
            queries.append((
                "MERGE (d:Disease {name: $name}) SET d.project='PET'",
                {"name": disease}
            ))
            for sym in rel.get("symptoms") or []:
                sym_clean = clean_text(sym)
                queries.append((
                    "MERGE (s:Symptom {name: $name}) SET s.project='PET'",
                    {"name": sym_clean}
                ))
                queries.append((
                    "MATCH (d:Disease {name: $disease}), (s:Symptom {name: $symptom}) "
                    "MERGE (d)-[:HAS_SYMPTOM {project:'PET'}]->(s)",
                    {"disease": disease, "symptom": sym_clean}
                ))

    return queries


if __name__ == "__main__":
    json_path = "../__002__extract_entity_relation/宠物食品实体关系细节提取结果.json"

    queries = generate_petfood_graph_queries(json_path)

    neo4j_client.run_multiple_cypher(queries)

    print("✅ 宠物食品图谱数据导入完成！")
