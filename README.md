# AI 小说创作记忆助手（Novel Assistant）

一个轻量级 AI 创作辅助系统，帮助作者记录、整理和召回创作灵感与设定。

## 核心理念

系统本质：**创作记忆库（Creative Memory System）**

- 帮助作者扩展创意
- 自动整理设定与剧情点
- 记录创作中的关键记忆
- 在后续创作时召回相关上下文
- 降低 AI 长篇创作中的"失忆"问题

**重要：系统不存"整章正文"，而是存"知识点（Memory Units）"**

## 系统架构

```
用户输入
   ↓
LLM结构化
   ↓
JSON Memory
   ↓
Embedding
   ↓
Chroma Vector DB
   ↓
Memory Retrieval
   ↓
拼接上下文
   ↓
LLM 创作建议
```

## MVP 功能范围

### 1. Memory Add
添加创作记忆，系统自动整理并存储。

### 2. Memory Search
根据当前创作内容检索相关记忆。

### 3. AI Suggestion
基于检索到的记忆给创作建议。

### 4. Memory Structuring
AI自动将用户输入整理为结构化记忆。

## Memory 数据模型

### Character Memory
人物相关设定。

```json
{
  "type": "character",
  "name": "顾北辰",
  "content": "害怕海水，小时候可能发生事故"
}
```

### Plot Memory
剧情点。

```json
{
  "type": "plot",
  "content": "第三章出现红怀表"
}
```

### Callback Memory
伏笔/回调。

```json
{
  "type": "callback",
  "content": "红怀表与父亲失踪有关"
}
```

## 项目结构

```
novel-assistant/
├── app.py                 # 主应用入口
├── memory.py              # Memory 管理
├── retrieve.py            # 检索和 embedding
├── suggest.py             # AI 建议生成
├── llm.py                 # LLM 封装
│
├── data/
│   ├── memories/          # 存储 JSON memories
│   ├── raw_notes/         # 原始笔记
│   └── chroma_db/         # 向量数据库
│
├── prompts/
│   ├── structure_prompt.txt     # 结构化 prompt
│   └── suggest_prompt.txt       # 建议生成 prompt
│
├── requirements.txt       # 依赖
└── README.md             # 项目文档
```

## 开发优先级

### 第一阶段（必须）
- ✅ add_memory
- ✅ search_memory
- ✅ AI结构化
- ✅ 本地存储

### 第二阶段（推荐）
- callback检测
- 人物一致性检查
- memory标签系统

### 第三阶段（未来）
- timeline memory
- relationship memory
- scene memory
- chapter summary

## MVP 成功标准

系统达到以下目标即视为成功：

```python
add_memory("顾北辰害怕海水")

search_memory("为什么顾北辰抗拒码头")
```

能够稳定召回：
- 海水恐惧
- 童年事故

并让AI在后续对话中保持设定一致。

## 技术选型

- **本地存储**：JSON 文件
- **向量数据库**：Chroma（本地运行）
- **Embedding 模型**：bge-small-zh（中文优化）
- **LLM**：支持 GPT、Claude、Qwen、DeepSeek 等

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据目录
mkdir -p data/memories data/raw_notes data/chroma_db

# 3. 运行应用
python app.py
```

## 使用示例

```python
from memory import MemoryManager
from retrieve import MemoryRetriever
from suggest import SuggestionGenerator

# 添加记忆
manager = MemoryManager()
manager.add_memory("顾北辰害怕海水，小时候可能出过事故")

# 搜索记忆
retriever = MemoryRetriever()
results = retriever.search_memory("为什么顾北辰抗拒码头")

# 生成建议
suggester = SuggestionGenerator()
suggestions = suggester.generate_suggestion(results)
```

## 许可证

MIT License

## 联系方式

作者：dongqinggu
