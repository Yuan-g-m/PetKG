
from neo4j import GraphDatabase
from neo4j.exceptions import CypherSyntaxError
from tqdm import tqdm
import json
from common.config import Config

conf = Config()


class Neo4jClient:
    def __init__(self, uri, user, password):
        """初始化 Neo4j 驱动"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()

    def check_cypher_syntax(self, query, parameters=None):
        """使用 EXPLAIN 检查 Cypher 语法是否正确"""
        explain_query = f"EXPLAIN {query}"
        try:
            with self.driver.session() as session:
                session.run(explain_query, parameters or {})
            return True, "语法正确"
        except CypherSyntaxError as e:
            return False, f"语法错误: {str(e)}"
        except Exception as e:
            return False, f"其他错误: {str(e)}"

    def run_cypher(self, query, parameters=None):
        """执行一条 Cypher 查询"""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def run_multiple_cypher(self, queries_with_params):
        """执行多条 Cypher 语句（事务 + tqdm 进度条）"""
        with self.driver.session() as session:
            def transaction_logic(tx):
                for query, params in tqdm(queries_with_params, desc="执行 Cypher 语句"):
                    tx.run(query, params or {})

            session.execute_write(transaction_logic)

    def get_pet_node_labels(self):
        """获取所有 project = 'PET' 的节点标签"""
        query = """
        MATCH (n)
        WHERE n.project = "PET"
        UNWIND labels(n) AS label
        RETURN DISTINCT label
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [record["label"] for record in result]

    def get_pet_relationship_structure(self):
        """获取 project='PET' 节点参与的三元组结构"""
        query = """
        MATCH (n)-[r]->(m)
        WHERE n.project = "PET"
        WITH head(labels(n)) AS from_label, type(r) AS rel_type, head(labels(m)) AS to_label
        RETURN DISTINCT from_label, rel_type, to_label
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

    def export_pet_metadata_to_json(self, output_path="pet_metadata.json"):
        """导出宠物图谱 schema 到 JSON"""
        with self.driver.session() as session:
            label_query = """
            MATCH (n)
            WHERE n.project = "PET"
            UNWIND labels(n) AS label
            RETURN DISTINCT label
            """
            labels = [record["label"] for record in session.run(label_query)]

            rel_query = """
            MATCH (n)-[r]-()
            WHERE n.project = "PET"
            RETURN DISTINCT type(r) AS rel_type
            """
            rel_types = [record["rel_type"] for record in session.run(rel_query)]

            triple_query = """
            MATCH (n)-[r]->(m)
            WHERE n.project = "PET"
            WITH head(labels(n)) AS from_label, type(r) AS rel_type, head(labels(m)) AS to_label
            RETURN DISTINCT from_label, rel_type, to_label
            """
            triples = [{
                "from": record["from_label"],
                "rel_type": record["rel_type"],
                "to": record["to_label"],
                "description": ""
            } for record in session.run(triple_query)]

            node_props_query = """
            MATCH (n)
            WHERE n.project = "PET"
            UNWIND labels(n) AS label
            UNWIND keys(n) AS prop
            RETURN DISTINCT label, prop
            ORDER BY label, prop
            """
            label_props = {}
            for record in session.run(node_props_query):
                label = record["label"]
                prop = record["prop"]
                if prop == "project":
                    continue
                label_props.setdefault(label, []).append({
                    "name": prop,
                    "description": ""
                })

            rel_props_query = """
            MATCH (n)-[r]->(m)
            WHERE n.project = "PET"
            UNWIND keys(r) AS prop
            RETURN DISTINCT type(r) AS rel_type, prop
            ORDER BY rel_type, prop
            """
            rel_type_props = {}
            for record in session.run(rel_props_query):
                rel_type = record["rel_type"]
                prop = record["prop"]
                rel_type_props.setdefault(rel_type, []).append({
                    "name": prop,
                    "description": ""
                })

            json_obj = {
                "labels": [
                    {
                        "name": label,
                        "description": "",
                        "properties": label_props.get(label, [])
                    } for label in labels
                ],
                "relationships": [
                    {
                        "type": rel,
                        "description": "",
                        "properties": rel_type_props.get(rel, [])
                    } for rel in rel_types
                ],
                "triples": triples
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_obj, f, ensure_ascii=False, indent=2)

            return output_path

    def get_all_disease_and_symptom_names(self):
        query = """
        MATCH (n)
        WHERE n:Symptom OR n:Disease
        RETURN n.name AS name, labels(n)[0] AS label
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [(record["name"], record["label"]) for record in result]

    def get_all_effect_names(self):
        query = """
        MATCH (n)
        WHERE n:Effect
        RETURN n.name AS name, labels(n)[0] AS label
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [(record["name"], record["label"]) for record in result]

    def __del__(self):
        self.close()


neo4j_client = Neo4jClient(conf.NEO4J_URI, conf.NEO4J_USER, conf.NEO4J_PASSWORD)
