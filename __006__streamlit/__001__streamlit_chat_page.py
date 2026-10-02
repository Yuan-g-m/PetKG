import json
import os
import uuid
from datetime import datetime
from typing import Any

import networkx as nx
import pandas as pd
import requests
import streamlit as st
from streamlit.components.v1 import html as components_html

from common.neo4j_client import neo4j_client
from tools.path_utils import resolve_from_project_root


st.set_page_config(
    page_title="宠知通 · 宠物知识图谱",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)


LABEL_META = {
    "PetFood": ("宠物食品", "#F59E0B"),
    "PetRecipe": ("宠物食谱", "#F97316"),
    "Disease": ("宠物疾病", "#EF4444"),
    "Symptom": ("宠物症状", "#FB7185"),
    "Effect": ("功效", "#10B981"),
    "EffectCategory": ("功效分类", "#14B8A6"),
    "PetFoodCategory": ("食品分类", "#22C55E"),
    "PetRecipeCategory": ("食谱分类", "#84CC16"),
    "NutritionType": ("营养特点", "#EAB308"),
    "PetType": ("适用宠物", "#6366F1"),
    "LifeStage": ("生命阶段", "#8B5CF6"),
    "Source": ("出处", "#A8A29E"),
}

REL_META = {
    "HAS_EFFECT": ("具有功效", "功效"),
    "ALLEVIATES_SYMPTOM": ("缓解症状", "症状"),
    "TREATS_DISEASE": ("调理疾病", "疾病"),
    "HAS_INGREDIENT": ("包含成分", "组成"),
    "HAS_NUTRITION": ("含营养特点", "营养"),
    "SUITS_PET_TYPE": ("适用宠物", "宠物"),
    "SUITS_LIFE_STAGE": ("适用阶段", "阶段"),
    "HAS_SYMPTOM": ("表现为症状", "症状"),
    "BELONGS_TO_EFFECT_CATEGORY": ("归属功效分类", "分类"),
    "BELONGS_TO_FOOD_CATEGORY": ("归属食品分类", "分类"),
    "BELONGS_TO": ("归属分类", "分类"),
    "FROM_SOURCE": ("来源于", "出处"),
    "ALIAS_OF": ("别名关联", "别名"),
}

PROPERTY_META = {
    "name": "名称",
    "alias": "别名",
    "brand": "品牌",
    "origin": "产地",
    "main_ingredient": "主要成分",
    "suitable_pet": "适用宠物",
    "processing": "加工工艺",
    "traits": "性状",
    "effect": "功效",
    "indication": "适用症状",
    "feeding": "喂食建议",
    "taboo": "禁忌",
    "effect_category": "功效分类",
    "food_category": "食品分类",
    "ingredients": "组成",
    "usage": "做法",
    "recipe_category": "食谱分类",
    "source": "出处",
    "std_source": "出处标准化",
}


CSS = """
<style>
:root {
    --pet-amber: #F59E0B;
    --pet-orange: #F97316;
    --pet-green: #10B981;
    --pet-ink: #3F2E2E;
    --pet-muted: #8A7B72;
    --pet-cream: #FFF8F0;
}

.stApp {
    background:
        radial-gradient(circle at 8% 8%, rgba(245, 158, 11, 0.13), transparent 26%),
        radial-gradient(circle at 92% 12%, rgba(16, 185, 129, 0.12), transparent 24%),
        linear-gradient(180deg, #FFFDF9 0%, #FFF6EC 100%);
    color: var(--pet-ink);
}

header[data-testid="stHeader"],
[data-testid="stToolbar"] {
    display: none !important;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 3rem;
    max-width: 1480px;
}

[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

.app-brand {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.35rem 0 0.4rem 0.2rem;
}

.app-brand-mark {
    width: 44px;
    height: 44px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 16px;
    font-size: 1.6rem;
    background: linear-gradient(135deg, #FFF2D8 0%, #FFD9A6 100%);
    border: 1px solid rgba(245, 158, 11, 0.28);
    box-shadow: 0 10px 22px rgba(245, 158, 11, 0.14);
}

.app-brand-name {
    font-size: 1.28rem;
    font-weight: 800;
    color: #3F2E2E;
    line-height: 1.15;
}

.app-brand-sub {
    color: #9A6B3F;
    font-size: 0.78rem;
    margin-top: 0.15rem;
}

div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 0.45rem !important;
    justify-content: flex-end !important;
}

body div[data-testid="stRadio"] > label {
    display: none !important;
}

div[data-testid="stRadio"] label {
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.42rem !important;
    padding: 0.52rem 0.78rem !important;
    margin: 0 !important;
    border-radius: 999px !important;
    border: 1px solid rgba(245, 158, 11, 0.2) !important;
    background: rgba(255, 255, 255, 0.68) !important;
    box-shadow: 0 5px 14px rgba(74, 50, 20, 0.04) !important;
    transition: all 0.18s ease !important;
    cursor: pointer !important;
    white-space: nowrap !important;
}

div[data-testid="stRadio"] label:hover {
    background: #FFF6E6 !important;
    border-color: rgba(245, 158, 11, 0.5) !important;
    transform: translateY(-1px);
}

div[data-testid="stRadio"] label:has(input:checked) {
    border-color: #F59E0B !important;
    background: linear-gradient(135deg, #FFF2D8 0%, #FFE1AF 100%) !important;
    box-shadow: 0 12px 28px rgba(245, 158, 11, 0.18) !important;
}

div[data-testid="stRadio"] label p {
    font-size: 0.86rem !important;
    font-weight: 800 !important;
    color: #3F2E2E !important;
    line-height: 1.4 !important;
    white-space: nowrap !important;
}

.current-module {
    margin-top: 0.8rem;
    padding: 0.6rem 0.75rem;
    border-radius: 12px;
    background: rgba(245, 158, 11, 0.12);
    color: #9A5B12;
    font-size: 0.82rem;
    font-weight: 700;
    text-align: center;
}

.sidebar-footer {
    margin-top: 1.2rem;
    padding: 0.75rem 0.6rem;
    border-top: 1px dashed rgba(154, 107, 63, 0.28);
    color: #8A7B72;
    font-size: 0.78rem;
    line-height: 1.6;
}

.hero {
    padding: 2.1rem 2.4rem;
    border-radius: 28px;
    background: linear-gradient(135deg, #FFF9F0 0%, #FFE8C7 58%, #E9F9EF 100%);
    border: 1px solid rgba(245, 158, 11, 0.22);
    box-shadow: 0 18px 50px rgba(120, 82, 30, 0.09);
    margin-bottom: 1.4rem;
}

.hero-eyebrow {
    font-size: 0.78rem;
    letter-spacing: 0.18em;
    color: var(--pet-orange);
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 0.45rem;
}

.hero-title {
    font-size: 2.25rem;
    line-height: 1.15;
    font-weight: 800;
    color: var(--pet-ink);
    margin: 0;
}

.hero-subtitle {
    margin-top: 0.65rem;
    color: #6E5B51;
    font-size: 1.02rem;
    line-height: 1.75;
}

.section-title {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--pet-ink);
    margin: 0.5rem 0 0.2rem 0;
}

.section-caption {
    color: var(--pet-muted);
    font-size: 0.92rem;
    margin-bottom: 0.8rem;
}

.conversation-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #3F2E2E;
    margin: 0.15rem 0 0.5rem 0;
}

.conversation-subtitle {
    color: #8A7B72;
    font-size: 0.82rem;
    line-height: 1.5;
    margin: -0.25rem 0 0.65rem 0;
}

.conversation-count {
    color: #9A6B3F;
    font-size: 0.78rem;
    font-weight: 700;
    margin: 0.55rem 0 0.35rem 0.15rem;
}

.conversation-empty {
    padding: 1.2rem 0.9rem;
    border-radius: 14px;
    border: 1px dashed rgba(154, 107, 63, 0.32);
    color: #8A7B72;
    font-size: 0.86rem;
    line-height: 1.65;
    text-align: center;
    background: rgba(255, 255, 255, 0.42);
}

div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    margin-top: 0.18rem !important;
    margin-bottom: 0.18rem !important;
}

div[data-testid="stHorizontalBlock"] button[kind="secondary"] p {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 178px;
}

.entity-card {
    padding: 1.1rem 1.2rem;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.82);
    border: 1px solid rgba(245, 158, 11, 0.16);
    box-shadow: 0 8px 22px rgba(74, 50, 20, 0.05);
    margin-bottom: 0.8rem;
}

.entity-name {
    font-size: 1.05rem;
    font-weight: 800;
    color: var(--pet-ink);
}

.entity-badge {
    display: inline-block;
    margin-top: 0.4rem;
    padding: 0.2rem 0.62rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    color: #FFFFFF;
}

.kv-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
}

.kv-table td {
    padding: 0.55rem 0.7rem;
    border-bottom: 1px solid #F1E4D8;
    vertical-align: top;
}

.kv-table td:first-child {
    width: 118px;
    color: #9A6B3F;
    font-weight: 700;
}

.graph-note {
    padding: 0.7rem 0.9rem;
    border-radius: 14px;
    background: #FFF1DF;
    color: #7C4A12;
    font-size: 0.88rem;
    margin-bottom: 0.8rem;
}

div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.82);
    border: 1px solid rgba(245, 158, 11, 0.16);
    border-radius: 18px;
    padding: 1rem 1.1rem;
    box-shadow: 0 8px 22px rgba(74, 50, 20, 0.05);
}

div[data-testid="stMetricValue"] {
    color: var(--pet-ink);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 999px;
    padding: 0.45rem 0.9rem;
    background: rgba(255, 255, 255, 0.66);
}
</style>
"""


def label_cn(label: str) -> str:
    return LABEL_META.get(label, (label, "#A8A29E"))[0]


def label_color(label: str) -> str:
    return LABEL_META.get(label, (label, "#A8A29E"))[1]


def rel_cn(rel: str) -> str:
    return REL_META.get(rel, (rel, ""))[0]


def prop_cn(prop: str) -> str:
    return PROPERTY_META.get(prop, prop)


def cypher(query: str, params: dict | None = None) -> list[dict[str, Any]]:
    try:
        return neo4j_client.run_cypher(query, params or {})
    except Exception as exc:
        st.error(f"图谱查询失败：{exc}")
        return []


@st.cache_data(show_spinner=False)
def load_schema() -> dict[str, Any]:
    path = resolve_from_project_root("__004__langgraph_agent/pet_metadata.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_overview() -> tuple[int, int, list[dict[str, Any]], list[dict[str, Any]]]:
    node_count = cypher("MATCH (n) WHERE n.project='PET' RETURN count(n) AS c")[0]["c"]
    rel_count = cypher("MATCH (n)-[r]->() WHERE n.project='PET' RETURN count(r) AS c")[0]["c"]
    labels = cypher(
        """
        MATCH (n)
        WHERE n.project='PET'
        UNWIND labels(n) AS label
        RETURN label, count(*) AS count
        ORDER BY count DESC
        """
    )
    rels = cypher(
        """
        MATCH (n)-[r]->()
        WHERE n.project='PET'
        RETURN type(r) AS rel, count(*) AS count
        ORDER BY count DESC
        """
    )
    return node_count, rel_count, labels, rels


def fetch_graph_snapshot(limit: int = 400) -> list[dict[str, Any]]:
    return cypher(
        """
        MATCH (n)-[r]->(m)
        WHERE n.project='PET'
        RETURN labels(n)[0] AS source_label, n.name AS source_name,
               type(r) AS rel,
               labels(m)[0] AS target_label, m.name AS target_name
        LIMIT 400
        """
    )


def fetch_nodes(label: str, search: str = "") -> list[dict[str, Any]]:
    return cypher(
        """
        MATCH (n)
        WHERE n.project='PET' AND $label IN labels(n)
          AND ($search = '' OR toLower(n.name) CONTAINS toLower($search))
        RETURN labels(n)[0] AS label, n.name AS name
        ORDER BY n.name
        LIMIT 200
        """,
        {"label": label, "search": search},
    )


def fetch_node_properties(label: str, name: str) -> dict[str, Any]:
    rows = cypher(
        """
        MATCH (n)
        WHERE n.project='PET' AND $label IN labels(n) AND n.name=$name
        RETURN properties(n) AS props, labels(n) AS labels
        LIMIT 1
        """,
        {"label": label, "name": name},
    )
    if not rows:
        return {}
    props = rows[0]["props"]
    props.pop("project", None)
    return props


def fetch_neighbors(label: str, name: str) -> list[dict[str, Any]]:
    return cypher(
        """
        MATCH (n)-[r]-(m)
        WHERE n.project='PET' AND $label IN labels(n) AND n.name=$name
        RETURN labels(n)[0] AS source_label, n.name AS source_name,
               type(r) AS rel,
               labels(m)[0] AS target_label, m.name AS target_name
        LIMIT 200
        """,
        {"label": label, "name": name},
    )


def fetch_shortest_path(
    source_label: str,
    source_name: str,
    target_label: str,
    target_name: str,
) -> list[dict[str, Any]]:
    return cypher(
        """
        MATCH p=shortestPath((a)-[*..4]-(b))
        WHERE a.project='PET' AND b.project='PET'
          AND $source_label IN labels(a) AND a.name=$source_name
          AND $target_label IN labels(b) AND b.name=$target_name
        UNWIND relationships(p) AS r
        RETURN labels(startNode(r))[0] AS source_label,
               startNode(r).name AS source_name,
               type(r) AS rel,
               labels(endNode(r))[0] AS target_label,
               endNode(r).name AS target_name
        """,
        {
            "source_label": source_label,
            "source_name": source_name,
            "target_label": target_label,
            "target_name": target_name,
        },
    )


def graph_elements(edge_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    node_map: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    for row in edge_rows:
        source_key = f"{row['source_label']}::{row['source_name']}"
        target_key = f"{row['target_label']}::{row['target_name']}"
        node_map[source_key] = {
            "id": source_key,
            "label": row["source_name"],
            "group": row["source_label"],
            "color": label_color(row["source_label"]),
        }
        node_map[target_key] = {
            "id": target_key,
            "label": row["target_name"],
            "group": row["target_label"],
            "color": label_color(row["target_label"]),
        }
        edges.append(
            {
                "source": source_key,
                "target": target_key,
                "label": rel_cn(row["rel"]),
                "rel": row["rel"],
            }
        )

    return list(node_map.values()), edges


NETWORK_TEMPLATE = """
<div id="petkg-network" style="width:100%;height:__HEIGHT__px;border:1px solid rgba(245,158,11,0.18);border-radius:20px;background:#FFFFFF;"></div>
<script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<script>
function renderPetGraph() {
  const container = document.getElementById('petkg-network');
  if (!window.vis) {
    container.innerHTML = '<div style="padding:24px;text-align:center;color:#8A7B72;">图谱组件加载失败，请检查网络连接。</div>';
    return;
  }
  const nodes = new vis.DataSet(__NODES__);
  const edges = new vis.DataSet(__EDGES__);
  const options = {
    nodes: {
      shape: 'dot',
      size: 24,
      borderWidth: 2,
      shadow: {enabled: true, size: 7, x: 0, y: 2},
      font: {face: 'Microsoft YaHei', color: '#3F2E2E', size: 14}
    },
    edges: {
      arrows: {to: {enabled: true, scaleFactor: 0.45}},
      color: {color: '#CBBDB0', highlight: '#F59E0B', hover: '#F97316'},
      smooth: {type: 'continuous'},
      font: {face: 'Microsoft YaHei', color: '#7B6B62', size: 10, align: 'middle', strokeWidth: 0}
    },
    physics: {
      enabled: true,
      solver: 'forceAtlas2Based',
      forceAtlas2Based: {gravitationalConstant: -70, centralGravity: 0.01, springLength: 130, springConstant: 0.08},
      stabilization: {enabled: true, iterations: 160}
    },
    interaction: {
      hover: true,
      tooltipDelay: 120,
      navigationButtons: true,
      keyboard: true,
      zoomView: true
    }
  };
  new vis.Network(container, {nodes: nodes, edges: edges}, options);
}
setTimeout(renderPetGraph, 220);
</script>
"""


def render_graph(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], height: int = 560) -> None:
    if not nodes:
        st.info("当前没有可展示的图谱数据。")
        return

    graph = nx.Graph()
    graph.add_nodes_from(node["id"] for node in nodes)
    graph.add_edges_from((edge["source"], edge["target"]) for edge in edges)
    positions = nx.spring_layout(graph, seed=42, k=1.4, iterations=80, scale=1200) if len(graph) > 1 else {}

    node_payload = []
    for node in nodes:
        payload = {
            "id": node["id"],
            "label": node["label"],
            "group": node["group"],
            "title": f"{label_cn(node['group'])} · {node['label']}",
            "color": {
                "background": node["color"],
                "border": "#FFFFFF",
                "highlight": {"background": "#3F2E2E", "border": "#FFFFFF"},
            },
            "value": 1,
        }
        if node["id"] in positions:
            payload["x"] = float(positions[node["id"]][0])
            payload["y"] = float(positions[node["id"]][1])
        node_payload.append(payload)

    edge_payload = []
    for edge in edges:
        edge_payload.append(
            {
                "from": edge["source"],
                "to": edge["target"],
                "label": edge["label"],
                "title": f"{edge['label']} · {rel_cn(edge['rel'])}",
            }
        )

    html_str = (
        NETWORK_TEMPLATE.replace("__HEIGHT__", str(height))
        .replace("__NODES__", json.dumps(node_payload, ensure_ascii=False).replace("</", "<\\/"))
        .replace("__EDGES__", json.dumps(edge_payload, ensure_ascii=False).replace("</", "<\\/"))
    )
    components_html(html_str, height=height, scrolling=True)


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-eyebrow">Pet Knowledge Graph</div>
            <h1 class="hero-title">🐾 宠知通 · 宠物知识图谱</h1>
            <div class="hero-subtitle">
                以图谱为核心，探索宠物食品、宠物食谱、疾病、症状与功效之间的知识网络；
                每一类实体、每一条关系都可以被看见、被追溯、被理解。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_top_nav() -> str:
    nav_options = {
        "overview": ("📊", "图谱总览"),
        "entity": ("🔍", "实体探索"),
        "path": ("🧭", "关系路径"),
        "chat": ("💬", "图谱智能探索"),
        "xiaohongshu": ("📝", "小红书图文"),
    }
    keys = list(nav_options.keys())
    if "nav_key" not in st.session_state:
        st.session_state.nav_key = "chat"

    brand_col, nav_col = st.columns([1.2, 4.2], gap="medium")
    with brand_col:
        st.markdown(
            """
            <div class="app-brand">
                <div class="app-brand-mark">🐾</div>
                <div>
                    <div class="app-brand-name">宠知通</div>
                    <div class="app-brand-sub">宠物知识图谱探索平台</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with nav_col:
        nav_key = st.radio(
            "顶部导航",
            keys,
            format_func=lambda key: f"{nav_options[key][0]} {nav_options[key][1]}",
            horizontal=True,
            label_visibility="collapsed",
            key="nav_key",
        )

    return nav_key


def render_overview() -> None:
    node_count, rel_count, labels, rels = fetch_overview()

    col1, col2, col3 = st.columns(3)
    col1.metric("图谱实体", f"{node_count:,}", "宠物领域实体节点")
    col2.metric("图谱关系", f"{rel_count:,}", "实体之间的语义连接")
    col3.metric("实体类型", str(len(labels)), "覆盖食品、食谱、疾病、症状等")

    st.markdown('<div class="section-title">图谱构成</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">从节点类型与关系类型观察整个知识网络的结构。</div>', unsafe_allow_html=True)

    left, right = st.columns([1.15, 1])
    with left:
        label_df = pd.DataFrame(labels)
        label_df["类型"] = label_df["label"].map(label_cn)
        st.bar_chart(label_df.set_index("类型")["count"], use_container_width=True)

    with right:
        rel_df = pd.DataFrame(rels)
        rel_df["关系"] = rel_df["rel"].map(rel_cn)
        rel_df["数量"] = rel_df["count"]
        st.dataframe(rel_df[["关系", "数量"]], use_container_width=True, height=290)

    with st.expander("查看图谱 Schema"):
        schema = load_schema()
        schema_rows = []
        for label_item in schema.get("labels", []):
            props = "、".join(p["name"] for p in label_item.get("properties", [])) or "—"
            schema_rows.append(
                {
                    "实体类型": label_cn(label_item["name"]),
                    "属性字段": props,
                }
            )
        st.dataframe(pd.DataFrame(schema_rows), use_container_width=True, height=360)

    st.markdown('<div class="section-title">全图谱预览</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">可拖拽、缩放、悬停查看实体与关系；颜色代表不同实体类型。</div>', unsafe_allow_html=True)
    edge_rows = fetch_graph_snapshot()
    nodes, edges = graph_elements(edge_rows)
    render_graph(nodes, edges, height=640)


def render_entity_explorer() -> None:
    labels = [row["label"] for row in cypher(
        """
        MATCH (n)
        WHERE n.project='PET'
        UNWIND labels(n) AS label
        RETURN DISTINCT label
        ORDER BY label
        """
    )]
    labels = [label for label in labels if label in LABEL_META]

    col1, col2 = st.columns([1, 1.4])
    with col1:
        default_label = labels.index("PetFood") if "PetFood" in labels else 0
        selected_label = st.selectbox("实体类型", labels, format_func=label_cn, key="entity_label", index=default_label)
    with col2:
        search = st.text_input("搜索实体名称", placeholder="例如：美毛、肠胃、幼犬", key="entity_search")

    nodes = fetch_nodes(selected_label, search)
    if not nodes:
        st.info("没有找到匹配实体。")
        return

    names = [node["name"] for node in nodes]
    selected_name = st.selectbox("选择实体", names, key="entity_name")
    props = fetch_node_properties(selected_label, selected_name)

    st.markdown(
        f"""
        <div class="entity-card">
            <div class="entity-name">🐕 {selected_name}</div>
            <span class="entity-badge" style="background:{label_color(selected_label)};">
                {label_cn(selected_label)}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if props:
        rows = "".join(
            f"<tr><td>{prop_cn(key)}</td><td>{value if value not in ('', None) else '—'}</td></tr>"
            for key, value in props.items()
            if key != "project"
        )
        st.markdown(
            f'<table class="kv-table"><tbody>{rows}</tbody></table>',
            unsafe_allow_html=True,
        )

    neighbors = fetch_neighbors(selected_label, selected_name)
    if not neighbors:
        st.info("该实体暂未连接到其他图谱节点。")
        return

    st.markdown('<div class="section-title">实体关联图谱</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">展示当前实体及其直接邻居，悬停节点可查看实体类型与名称。</div>', unsafe_allow_html=True)
    neighbor_nodes, neighbor_edges = graph_elements(neighbors)
    render_graph(neighbor_nodes, neighbor_edges, height=540)

    st.markdown('<div class="section-title">直接关联列表</div>', unsafe_allow_html=True)
    neighbor_df = pd.DataFrame(
        [
            {
                "关系": rel_cn(row["rel"]),
                "关联实体": f"{label_cn(row['target_label'])} · {row['target_name']}",
            }
            for row in neighbors
        ]
    )
    st.dataframe(neighbor_df, use_container_width=True, height=340)


def render_path_explorer() -> None:
    labels = [row["label"] for row in cypher(
        """
        MATCH (n)
        WHERE n.project='PET'
        UNWIND labels(n) AS label
        RETURN DISTINCT label
        ORDER BY label
        """
    )]
    labels = [label for label in labels if label in LABEL_META]

    st.markdown('<div class="section-title">关系路径探索</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">选择两个实体，查看它们之间最短的知识图谱路径。</div>', unsafe_allow_html=True)

    source_default = labels.index("PetFood") if "PetFood" in labels else 0
    target_default = labels.index("Effect") if "Effect" in labels else (1 if len(labels) > 1 else 0)

    col1, col2 = st.columns(2)
    with col1:
        source_label = st.selectbox("起点类型", labels, format_func=label_cn, key="path_source_label", index=source_default)
    with col2:
        target_label = st.selectbox("终点类型", labels, format_func=label_cn, key="path_target_label", index=target_default)

    source_nodes = fetch_nodes(source_label)
    target_nodes = fetch_nodes(target_label)
    source_names = [node["name"] for node in source_nodes]
    target_names = [node["name"] for node in target_nodes]

    default_edge = cypher(
        """
        MATCH (a)-[r]->(b)
        WHERE a.project='PET' AND b.project='PET'
          AND $source_label IN labels(a) AND $target_label IN labels(b)
        RETURN a.name AS source_name, b.name AS target_name
        LIMIT 1
        """,
        {"source_label": source_label, "target_label": target_label},
    )
    default_source_name = default_edge[0]["source_name"] if default_edge else (source_names[0] if source_names else None)
    default_target_name = default_edge[0]["target_name"] if default_edge else (target_names[0] if target_names else None)
    source_index = source_names.index(default_source_name) if default_source_name in source_names else 0
    target_index = target_names.index(default_target_name) if default_target_name in target_names else 0

    col3, col4 = st.columns(2)
    with col3:
        source_name = st.selectbox("起点实体", source_names, key="path_source_name", index=source_index)
    with col4:
        target_name = st.selectbox("终点实体", target_names, key="path_target_name", index=target_index)

    if st.button("查找最短路径", type="primary", use_container_width=True):
        if source_label == target_label and source_name == target_name:
            st.info("起点和终点相同，无需查找路径。")
            return

        path_rows = fetch_shortest_path(source_label, source_name, target_label, target_name)
        if not path_rows:
            st.warning("在当前图谱中没有找到 4 跳以内的关联路径。")
            return

        nodes, edges = graph_elements(path_rows)
        st.markdown('<div class="graph-note">已找到最短关联路径，图中高亮部分为路径经过的实体与关系。</div>', unsafe_allow_html=True)
        render_graph(nodes, edges, height=500)

        path_df = pd.DataFrame(
            [
                {
                    "起点": f"{label_cn(row['source_label'])} · {row['source_name']}",
                    "关系": rel_cn(row["rel"]),
                    "终点": f"{label_cn(row['target_label'])} · {row['target_name']}",
                }
                for row in path_rows
            ]
        )
        st.dataframe(path_df, use_container_width=True, height=300)


def conversation_file() -> str:
    return resolve_from_project_root("data/conversations.json")


def load_conversations() -> list[dict[str, Any]]:
    path = conversation_file()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("conversations", [])
    except Exception:
        return []


def save_conversations(conversations: list[dict[str, Any]]) -> None:
    path = conversation_file()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"conversations": conversations}, f, ensure_ascii=False, indent=2)


def conversation_title(messages: list[dict[str, Any]]) -> str:
    for message in messages:
        if message.get("role") == "user" and message.get("content"):
            title = message["content"].strip().replace("\n", " ")
            return title[:18] or "新对话"
    return "新对话"


def upsert_conversation(conv_id: str, messages: list[dict[str, Any]]) -> None:
    conversations = load_conversations()
    now = datetime.now().isoformat()
    existing = next((item for item in conversations if item.get("id") == conv_id), None)
    if existing:
        existing["messages"] = messages
        existing["title"] = conversation_title(messages)
        existing["updated_at"] = now
    else:
        conversations.append(
            {
                "id": conv_id,
                "title": conversation_title(messages),
                "created_at": now,
                "updated_at": now,
                "messages": messages,
            }
        )
    save_conversations(conversations)


def delete_conversation(conv_id: str) -> None:
    conversations = [item for item in load_conversations() if item.get("id") != conv_id]
    save_conversations(conversations)
    if st.session_state.get("current_conversation_id") == conv_id:
        st.session_state.current_conversation_id = str(uuid.uuid4())
        st.session_state.messages = []


def create_new_conversation() -> None:
    st.session_state.current_conversation_id = str(uuid.uuid4())
    st.session_state.messages = []


def select_conversation(conversation: dict[str, Any]) -> None:
    st.session_state.current_conversation_id = conversation["id"]
    st.session_state.messages = list(conversation.get("messages", []))


def call_graph_ai_stream(user_content: str, history: list[dict[str, Any]] | None = None):
    session_id = st.session_state.setdefault("session_id", str(uuid.uuid4()))
    user_id = st.session_state.setdefault("user_id", "user_01")
    payload = {
        "data": {
            "user_id": user_id,
            "session_id": session_id,
            "user_content": user_content,
            "history": (history or [])[-8:],
        }
    }
    try:
        with requests.post(
            "http://127.0.0.1:8000/process/stream",
            json=payload,
            stream=True,
            timeout=240,
            proxies={"http": None, "https": None},
            headers={"Connection": "close", "Cache-Control": "no-cache"},
        ) as resp:
            if resp.status_code != 200:
                yield f"图谱智能服务暂时不可用：HTTP {resp.status_code}"
                return
            for chunk in resp.iter_content(chunk_size=64):
                if chunk:
                    yield chunk.decode("utf-8", errors="replace")
    except Exception as exc:
        yield f"图谱智能服务暂时不可用：{exc}"


def render_graph_chat() -> None:
    if "current_conversation_id" not in st.session_state or not st.session_state.current_conversation_id:
        create_new_conversation()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    conversations = load_conversations()
    current_id = st.session_state.current_conversation_id
    left, right = st.columns([1, 2.65], gap="medium")

    with left:
        st.markdown('<div class="conversation-title">对话历史</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="conversation-subtitle">查看、切换或删除已保存的会话</div>',
            unsafe_allow_html=True,
        )

        if st.button("＋ 新建对话", use_container_width=True, key="new_conversation_button"):
            create_new_conversation()
            st.rerun()

        st.markdown(
            f'<div class="conversation-count">共 {len(conversations)} 个历史对话</div>',
            unsafe_allow_html=True,
        )

        ordered = sorted(conversations, key=lambda item: item.get("updated_at", ""), reverse=True)
        if not ordered:
            st.markdown(
                '<div class="conversation-empty">还没有历史对话<br>从右侧输入问题开始一次新的图谱探索吧</div>',
                unsafe_allow_html=True,
            )

        for conversation in ordered[:40]:
            conv_id = conversation.get("id")
            title = conversation.get("title") or "新对话"
            updated_at = conversation.get("updated_at", "")
            try:
                time_label = datetime.fromisoformat(updated_at).strftime("%m-%d %H:%M")
            except Exception:
                time_label = ""
            active = conv_id == current_id
            button_col, delete_col = st.columns([4.4, 1])
            with button_col:
                if st.button(
                    f"{title} · {time_label}",
                    key=f"conversation_{conv_id}",
                    use_container_width=True,
                    type="primary" if active else "secondary",
                    help="切换到此对话",
                ):
                    select_conversation(conversation)
                    st.rerun()
            with delete_col:
                if st.button("🗑", key=f"delete_{conv_id}", help="删除该对话"):
                    delete_conversation(conv_id)
                    st.rerun()

    with right:
        st.markdown('<div class="section-title">图谱智能探索</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-caption">输入宠物养护问题，系统会先在图谱中识别实体与关系，再生成可解释的回答。</div>',
            unsafe_allow_html=True,
        )

        message_container = st.container()
        with message_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        prompt = st.chat_input("例如：狗狗掉毛应该关注哪些功效和食谱？")
        if not prompt:
            return

        st.session_state.messages.append({"role": "user", "content": prompt})
        with message_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("正在图谱中检索实体与关系..."):
                    history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1]
                    ]
                    answer = st.write_stream(call_graph_ai_stream(prompt, history))
                st.caption("答案由知识图谱实体检索 + 大模型生成")

        st.session_state.messages.append({"role": "assistant", "content": answer})
        upsert_conversation(current_id, st.session_state.messages)
        st.rerun()


def call_xiaohongshu_api(user_content: str) -> dict[str, Any]:
    session_id = st.session_state.setdefault("session_id", str(uuid.uuid4()))
    user_id = st.session_state.setdefault("user_id", "user_01")
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.get("messages", [])
    ][-8:]
    payload = {
        "data": {
            "user_id": user_id,
            "session_id": session_id,
            "user_content": user_content,
            "history": history,
        }
    }
    try:
        resp = requests.post(
            "http://127.0.0.1:8000/process/xiaohongshu",
            json=payload,
            timeout=240,
            proxies={"http": None, "https": None},
        )
        if resp.status_code != 200:
            return {"title": "", "content": f"服务暂时不可用：HTTP {resp.status_code}", "image_path": ""}
        return resp.json().get("result", {})
    except Exception as exc:
        return {"title": "", "content": f"服务暂时不可用：{exc}", "image_path": ""}


def render_copy_button(label: str, text: str, button_id: str) -> None:
    if not text:
        return
    safe_text = json.dumps(text, ensure_ascii=False)
    components_html(
        f"""
        <button id="{button_id}" style="
            display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border:1px solid #F0B35C;
            border-radius:999px;background:#FFF6E6;color:#9A5B12;font-weight:700;font-size:13px;cursor:pointer;
            box-shadow:0 6px 14px rgba(154,91,18,0.08);transition:all .2s ease;
        ">{label}</button>
        <script>
        (function(){{
            const btn = document.getElementById('{button_id}');
            const text = {safe_text};
            btn.addEventListener('click', async () => {{
                try {{
                    await navigator.clipboard.writeText(text);
                    btn.textContent = '已复制';
                }} catch (e) {{
                    const ta = document.createElement('textarea');
                    ta.value = text;
                    ta.style.position = 'fixed';
                    ta.style.opacity = '0';
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    btn.textContent = '已复制';
                }}
                setTimeout(() => {{ btn.textContent = '{label}'; }}, 1400);
            }});
        }})();
        </script>
        """,
        height=52,
    )


def render_xiaohongshu() -> None:
    st.markdown('<div class="section-title">小红书图文生成</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">输入宠物养护主题，生成可直接复制的小红书标题、正文和配图草稿。实际发布需在小红书 App 或网页端完成。</div>',
        unsafe_allow_html=True,
    )

    with st.form("xiaohongshu_generate_form"):
        topic = st.text_area(
            "主题 / 灵感",
            placeholder="例如：狗狗掉毛养护攻略、猫咪换粮注意事项、仓鼠日常喂养清单",
            height=110,
        )
        submitted = st.form_submit_button("生成图文", type="primary", use_container_width=True)

    if submitted:
        if not topic.strip():
            st.warning("请先输入一个主题或灵感。")
            return
        with st.spinner("正在生成小红书标题、正文与配图..."):
            result = call_xiaohongshu_api(topic.strip())
        st.session_state.xiaohongshu_result = result

    result = st.session_state.get("xiaohongshu_result") or {}
    title = (result.get("title") or "").strip()
    content = (result.get("content") or "").strip()
    image_path = (result.get("image_path") or "").strip()

    if title or content:
        st.markdown('<div class="entity-card">', unsafe_allow_html=True)
        st.markdown('<div class="entity-name">生成结果</div>', unsafe_allow_html=True)
        st.markdown("**标题**")
        st.markdown(title)
        render_copy_button("复制标题", title, "copy_xhs_title")
        st.markdown("**正文**")
        st.markdown(content)
        render_copy_button("复制正文", content, "copy_xhs_content")
        st.markdown("</div>", unsafe_allow_html=True)

        if image_path and os.path.exists(image_path):
            st.image(image_path, caption="生成配图", use_container_width=True)
        else:
            st.info("配图未生成或未配置图片服务密钥。请检查 `.env` 中的 `JIMENG_AK` / `JIMENG_SK`，重启服务后重试。文案仍可正常复制使用。")


def render_sidebar() -> str:
    nav_options = {
        "overview": ("📊", "图谱总览", "全局结构 · 分布预览"),
        "entity": ("🔍", "实体探索", "搜索实体 · 查看邻居"),
        "path": ("🧭", "关系路径", "起点终点 · 最短路径"),
        "chat": ("💬", "图谱智能探索", "图谱检索 · 对话解释"),
        "xiaohongshu": ("📝", "小红书图文", "文案生成 · 配图制作"),
    }

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-name">🐾 宠知通</div>
                <div class="sidebar-brand-sub">宠物知识图谱探索平台</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        node_count = cypher("MATCH (n) WHERE n.project='PET' RETURN count(n) AS c")[0]["c"]
        rel_count = cypher("MATCH (n)-[r]->() WHERE n.project='PET' RETURN count(r) AS c")[0]["c"]
        label_count = cypher(
            """
            MATCH (n)
            WHERE n.project='PET'
            UNWIND labels(n) AS label
            RETURN count(DISTINCT label) AS c
            """
        )[0]["c"]
        st.markdown(
            f"""
            <div class="sidebar-stats">
                <div class="sidebar-stat">
                    <div class="sidebar-stat-value">{node_count}</div>
                    <div class="sidebar-stat-label">实体节点</div>
                </div>
                <div class="sidebar-stat">
                    <div class="sidebar-stat-value">{rel_count}</div>
                    <div class="sidebar-stat-label">关系连接</div>
                </div>
                <div class="sidebar-stat">
                    <div class="sidebar-stat-value">{label_count}</div>
                    <div class="sidebar-stat-label">实体类型</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-nav-title">功能导航</div>', unsafe_allow_html=True)
        nav_key = st.radio(
            "功能导航",
            list(nav_options.keys()),
            format_func=lambda key: f"{nav_options[key][0]}  {nav_options[key][1]}　·　{nav_options[key][2]}",
            label_visibility="collapsed",
        )

        selected_title = nav_options[nav_key][1]
        st.markdown(
            f'<div class="current-module">当前模块：{selected_title}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="sidebar-footer">
                数据来自本地 Neo4j 宠物知识图谱。<br>
                所有探索均以实体与关系为核心。
            </div>
            """,
            unsafe_allow_html=True,
        )
        return nav_key


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    nav = render_top_nav()

    with st.spinner("正在加载模块..."):
        if nav == "overview":
            render_hero()
            render_overview()
        elif nav == "entity":
            render_entity_explorer()
        elif nav == "path":
            render_path_explorer()
        elif nav == "chat":
            render_graph_chat()
        else:
            render_xiaohongshu()


if __name__ == "__main__":
    main()
