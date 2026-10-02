# 宠知通 · 宠物知识图谱探索平台

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.0%2B-red.svg)](https://streamlit.io)
[![Neo4j](https://img.shields.io/badge/neo4j-5.0%2B-green.svg)](https://neo4j.com)

一个以知识图谱为核心的宠物养护探索平台，集成了宠物食品和食谱数据采集、实体关系抽取、图数据库构建以及图谱智能探索功能。

> 本项目由「中医知识图谱」整体换皮而来：领域标记由 `TCM` 改为 `PET`，核心实体由中药/方剂映射为宠物食品/宠物食谱，依赖复用 FinRAG，中间件改为项目内自带的本地 Neo4j 4.4 与 JDK 11，可一键启动。

## 📋 项目简介

本项目旨在构建一个完整的宠物知识图谱，并围绕图谱提供可视化探索与智能检索。系统主要包含以下功能：

- 🕷️ **数据采集**：自动爬取宠物百科网站的宠物食品和食谱信息
- 🧠 **实体抽取**：基于大语言模型提取宠物食品和食谱的结构化实体信息
- 📊 **知识图谱构建**：将结构化数据导入 Neo4j 图数据库
- 🤖 **图谱智能探索**：基于 LangGraph 多代理系统的图谱实体识别与检索
- 💻 **Web 界面**：基于 Streamlit 的用户友好界面

## 🏗️ 项目架构

```
PetKG/
├── __001__crawler/                         # 数据采集模块
│   ├── __000__获取网页内容通用方法.py
│   ├── __001__get_recipe_menu_list.py      # 宠物食谱列表获取
│   ├── __002__get_recipe_detail_info.py    # 宠物食谱详情获取
│   ├── __003__get_petfood_menu_list.py     # 宠物食品列表获取
│   └── __004__get_petfood_detail_list.py   # 宠物食品详情获取
├── __002__extract_entity_relation/         # 实体关系抽取模块
│   ├── __001__extract_recipe_entity.py     # 宠物食谱实体抽取
│   ├── __002__extract_petfood_entity.py    # 宠物食品实体抽取
│   ├── __003__extract_recipe_entity_relation_detail.py
│   ├── __004__extract_petfood_entity_relation_detail.py
│   └── __005__parse_recipe_source.py
├── __003__create_neo4j/                    # Neo4j 图数据库构建
│   ├── __001__create_recipe_entity.py      # 宠物食谱实体创建
│   ├── __002__create_petfood_entity.py     # 宠物食品实体创建
│   ├── __003__create_recipe_relation.py    # 宠物食谱关系创建
│   └── __004__create_petfood_relation.py   # 宠物食品关系创建
├── __004__langgraph_agent/                 # 图谱检索代理与向量嵌入
│   ├── __001__get_neo4j_json.py
│   ├── __002__disease_symptom_embedding_out.py
│   ├── __003__effect_embedding_out.py
│   ├── __004__langgraph_more_agent.py      # 主代理逻辑
│   ├── agent_state.py                      # 代理状态管理
│   ├── pet_metadata.json                   # 宠物图谱 schema
│   └── my_agents/                          # 各种专业代理
│       ├── pet_question_classifier_agent.py
│       ├── symptom_or_disease_checker_agent.py
│       ├── symptom_or_disease_entity_embedding_matcher_agent.py
│       ├── effect_checker_agent.py
│       ├── effect_entity_embedding_matcher_agent.py
│       ├── cypher_query_generator_agent.py
│       ├── direct_llm_answer_agent.py
│       ├── final_answer_mixer_agent.py
│       ├── xiaohongshu_intent_classifier_agent.py
│       ├── xiaohongshu_pet_post_output_agent.py
│       └── xiaohongshu_image_generator_agent.py
├── __005__fastapi/                         # FastAPI 服务
│   ├── my_fastapi.py
│   └── my_fastapi_test.py
├── __006__streamlit/                       # Web 应用界面
│   ├── __001__streamlit_chat_page.py       # 聊天界面
│   └── __002__auto_publish_xiaohongshu.py  # 小红书自动发布示例
├── common/                                 # 公共模块
│   ├── config.py                           # 环境配置读取（.env）
│   ├── embedding_model.py
│   ├── llm.py
│   └── neo4j_client.py
├── tools/
│   └── path_utils.py                       # 路径工具
├── data/                                   # 宠物示例数据集
│   ├── 宠物食品/                           # 宠物食品详情文件
│   ├── 宠物食谱/                           # 宠物食谱详情文件
│   ├── 宠物食品列表.xlsx / .csv
│   └── 宠物食谱列表.xlsx / .csv
├── main.py                                 # 主程序入口（启动 Streamlit）
├── requirements.txt                        # 依赖（复用 FinRAG + 补充）
├── docker-compose.yml                      # 中间件（复用 FinRAG + Neo4j）
├── config.ini.example
├── .env.example
└── .gitignore
```

## 🚀 快速开始

### 一键启动

项目已配置为开箱即用，本机无需 Docker，也无需手动启动 Neo4j：

```powershell
git clone <你的仓库地址> PetKG
cd PetKG
Copy-Item .env.example .env
# 编辑 .env，填入自己的 LLM Key；如已有独立 Conda 环境，可设置 PETKG_PYTHON
$env:PETKG_PYTHON = "D:\path\to\python.exe"
```

1. 双击 `启动PetKG.bat`
2. 等待脚本依次启动 Neo4j、FastAPI、Streamlit
3. 浏览器自动打开 `http://127.0.0.1:8501`

也可以在当前目录执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start.ps1
```

停止服务请双击 `停止PetKG.bat`。

原入口 `python main.py` 仍可用于只启动 Streamlit，但需先确保 Neo4j 与 FastAPI 已在运行。

### 启动项说明

- Python 环境：优先读取 `PETKG_PYTHON`；未设置时兼容本机 `D:\agentFinal\FinRAG\Miniconda3\envs\PetKG`
- Neo4j：`runtime\neo4j-community-4.4.41`
- JDK：`runtime\jdk-11.0.32.1+1`
- FastAPI：`http://127.0.0.1:8000`
- Streamlit：`http://127.0.0.1:8501`

`start.ps1` 会自动设置 `PYTHONPATH`、`SSL_CERT_FILE`、`NO_PROXY` 和 Neo4j 所需环境变量，并写入 `runtime\logs` 日志目录。

> 注意：`runtime/` 包含 Neo4j、JDK 与本地数据库文件，体积较大且不适合提交到 Git，因此仓库默认忽略该目录。克隆后请将本地运行时目录放入 `runtime/`，或按 `docker-compose.yml` 自行准备中间件。

## 📖 功能模块详解

### 1. 数据采集 (`__001__crawler`)

负责从宠物百科网站采集数据：

- **宠物食谱数据采集**：获取食谱列表和详细信息
- **宠物食品数据采集**：获取食品列表和详细信息
- **数据存储**：以 Excel 和文本文件形式保存原始数据

### 2. 实体关系抽取 (`__002__extract_entity_relation`)

使用大语言模型从原始文本中抽取结构化信息：

- **宠物食品实体抽取**：名称、别名、品牌、产地、主要成分、适用宠物、功效等
- **宠物食谱实体抽取**：食谱名、组成、功效、适用症状、做法等
- **关系抽取**：宠物食品/食谱与疾病、症状、功效之间的关系

### 3. 知识图谱构建 (`__003__create_neo4j`)

将结构化数据导入 Neo4j 图数据库：

- **实体节点创建**：宠物食品、宠物食谱、疾病、症状、功效、营养特点、生命阶段等节点
- **关系边创建**：调理、包含、适用、缓解等关系
- **图谱优化**：索引创建和数据验证

### 4. 图谱智能探索 (`__004__langgraph_agent`)

基于 LangGraph 构建的多代理图谱检索系统：

- **问题分类代理**：判断是否为宠物领域问题
- **实体识别代理**：识别症状、疾病、功效等实体
- **知识检索代理**：从知识图谱中检索相关信息
- **答案生成代理**：综合信息生成最终答案

### 5. Web 界面 (`__006__streamlit`)

基于 Streamlit 的用户交互界面，支持多轮对话、流式响应与小红书自动发布。

## 🧪 示例查询

- "狗狗掉毛应该吃什么？"
- "化毛膏的作用是什么？"
- "肠胃不适的猫咪适合什么食谱？"
- "幼犬补钙吃什么好？"

## 📊 图谱 Schema

| 实体标签 | 说明 |
| --- | --- |
| `PetFood` | 宠物食品/营养品 |
| `PetRecipe` | 宠物食谱 |
| `Disease` | 宠物疾病 |
| `Symptom` | 宠物症状 |
| `Effect` | 功效 |
| `PetType` | 适用宠物类型 |
| `NutritionType` | 营养特点 |
| `LifeStage` | 适用生命阶段 |
| `EffectCategory` / `PetFoodCategory` / `PetRecipeCategory` / `Source` | 分类与出处 |

## 🔧 技术栈

- **后端框架**：LangChain, LangGraph
- **数据库**：Neo4j
- **前端界面**：Streamlit
- **数据处理**：Pandas, BeautifulSoup
- **向量检索**：FAISS
- **AI 模型**：DeepSeek / OpenAI 兼容 LLM

## ⚠️ 免责声明

本系统提供的宠物养护信息仅供参考，宠物出现疾病症状时请及时咨询专业兽医。

## 📞 联系方式

如有问题或建议，请提交 GitHub Issue 或联系项目维护者。
