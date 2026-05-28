# AI 小说创作记忆助手（MVP）设计文档 v0.1

## 1. 项目目标

构建一个轻量级 AI 创作辅助系统。

系统职责：

1. 帮助作者扩展创意
2. 自动整理设定与剧情点
3. 记录创作中的关键记忆
4. 在后续创作时召回相关上下文
5. 降低 AI 长篇创作中的"失忆"问题

系统不是：

* 自动小说生成器
* 全自动剧情规划器
* 复杂 Narrative OS

作者始终拥有最终创作权。

---

## 2. 核心理念

### 2.1 系统定位

系统本质：

"创作记忆库（Creative Memory System）"

而不是：

"小说数据库"。

---

### 2.2 核心思想

用户输入：

* 灵感
* 剧情点
* 人物设定
* 伏笔
* 世界观

AI负责：

* 整理
* 格式化
* 建立记忆
* 检索相关信息
* 提供创作建议

---

### 2.3 最重要原则

系统不存"整章正文"。

系统存：

"知识点（Memory Units）"

例如：

* 顾北辰害怕海水
* 红怀表属于父亲
* 林雨晴开始怀疑顾北辰

而不是：

* 第1章全文
* 第2章全文

---

## 3. MVP 功能范围

MVP阶段只实现：

### 3.1 Memory Add

添加创作记忆。

例如：

输入：

"顾北辰害怕海水，小时候可能出过事故"

系统自动整理并存储。

---

### 3.2 Memory Search

根据当前创作内容检索相关记忆。

例如：

查询：

"为什么顾北辰抗拒码头"

系统召回：

* 害怕海水
* 童年事故

---

### 3.3 AI Suggestion

基于检索到的记忆给创作建议。

例如：

* 可以加入PTSD反应
* 可以安排雨夜回忆
* 可以关联父亲失踪事件

---

### 3.4 Memory Structuring

AI自动将用户输入整理为结构化记忆。

---

## 4. Memory 数据模型

MVP只保留三类 memory。

避免过度设计。

---

### 4.1 Character Memory

人物相关设定。

示例：

```json
{
  "type": "character",
  "name": "顾北辰",
  "content": "害怕海水，小时候可能发生事故"
}
```

---

### 4.2 Plot Memory

剧情点。

示例：

```json
{
  "type": "plot",
  "content": "第三章出现红怀表"
}
```

---

### 4.3 Callback Memory

伏笔/回调。

示例：

```json
{
  "type": "callback",
  "content": "红怀表与父亲失踪有关"
}
```

---

## 5. 系统架构

整体架构：

```text
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

---

## 6. 技术选型

### 6.1 本地数据存储

推荐：

JSON 文件

原因：

* 简单
* 可读
* 易调试
* 易迁移

目录：

```text
data/
├── memories/
├── raw_notes/
└── chroma_db/
```

---

### 6.2 向量数据库

推荐：

Chroma

原因：

* 本地运行
* API简单
* 快速开发
* 足够支持MVP

---

### 6.3 Embedding 模型

推荐：

bge-small-zh

原因：

* 中文效果较好
* 本地可运行
* 速度快

---

### 6.4 LLM

任选：

* GPT
* Claude
* Qwen
* DeepSeek

系统不绑定模型。

---

## 7. 项目目录结构

推荐：

```text
novel-assistant/
├── app.py
├── memory.py
├── retrieve.py
├── suggest.py
├── llm.py
│
├── data/
│   ├── memories/
│   ├── raw_notes/
│   └── chroma_db/
│
└── prompts/
    ├── structure_prompt.txt
    └── suggest_prompt.txt
```

---

## 8. 核心模块设计

### 8.1 memory.py

职责：

* 新增 memory
* 删除 memory
* 更新 memory
* 保存 JSON

核心接口：

```python
add_memory()
update_memory()
delete_memory()
```

---

### 8.2 retrieve.py

职责：

* embedding
* 向量检索
* memory召回

核心接口：

```python
search_memory(query)
```

---

### 8.3 suggest.py

职责：

* 拼接上下文
* 调用LLM
* 输出创作建议

核心接口：

```python
generate_suggestion()
```

---

### 8.4 llm.py

职责：

统一封装 LLM API。

避免业务代码直接调用模型。

---

## 9. Memory 生命周期

### 9.1 创建

用户输入创意。

AI整理为结构化 memory。

写入：

* JSON
* Chroma

---

### 9.2 检索

根据用户当前问题：

* embedding query
* vector search
* 返回相关 memory

---

### 9.3 更新

当设定修改时：

* 更新 JSON
* 删除旧 embedding
* 重建 embedding

---

## 10. Prompt 设计

### 10.1 Structure Prompt

目标：

将用户自由输入整理为结构化 memory。

示例：

```text
请将以下内容整理为小说创作记忆。

要求：
1. 保留核心设定
2. 尽量简洁
3. 不扩写剧情
4. 输出JSON
```

---

### 10.2 Suggest Prompt

目标：

基于 memory 给创作建议。

示例：

```text
你是一个小说创作助手。

你的职责：
1. 基于已有记忆给建议
2. 保持设定一致
3. 不替用户决定剧情
4. 提供可能性，而不是结论
```

---

## 11. 创作工作流

推荐工作流：

### Step1

用户记录灵感：

"顾北辰看到海水会紧张"

---

### Step2

AI结构化：

```json
{
  "type": "character",
  "name": "顾北辰",
  "content": "害怕海水"
}
```

---

### Step3

系统存储：

* JSON
* embedding
* Chroma

---

### Step4

后续创作时：

用户输入：

"这一章怎么制造压迫感？"

系统自动检索：

* 海水恐惧
* 码头
* 童年事故

---

### Step5

AI生成建议：

* 可以加入潮湿环境
* 可以强化呼吸反应
* 可以触发回忆

---

## 12. 当前阶段不做的事情

MVP阶段不实现：

* Graph Database
* 自动剧情规划
* 多Agent系统
* 自动写完整章节
* 世界状态模拟
* 自动冲突推进
* 时间线引擎

避免系统复杂度失控。

---

## 13. 开发优先级

### 第一阶段（必须）

* add_memory
* search_memory
* AI结构化
* 本地存储

---

### 第二阶段（推荐）

* callback检测
* 人物一致性检查
* memory标签系统

---

### 第三阶段（未来）

* timeline memory
* relationship memory
* scene memory
* chapter summary

---

## 14. MVP 成功标准

系统达到以下目标即视为成功：

```python
add_memory("顾北辰害怕海水")

search_memory("为什么顾北辰抗拒码头")
```

能够稳定召回：

* 海水恐惧
* 童年事故

并让AI在后续对话中保持设定一致。

---

## 15. 最终定位

本系统最终目标：

"为创作者提供长期稳定的 AI 创作记忆能力"

而不是：

"替代作者创作"。
