# 版本历史

## [v0.1.0] - 2026-05-30

### 🎉 初版发布 - 可用的基线

这是 novel-assistant 的第一个稳定可用版本，包含核心功能和基础架构。

### ✨ 功能特性

#### 1. 记忆管理系统 (`memory.py`)
- ✅ 多种记忆类型支持：角色、剧情、伏笔
- ✅ JSON 持久化存储
- ✅ UUID 唯一标识
- ✅ 时间戳记录（创建/更新时间）
- ✅ 批量导入/导出功能

#### 2. 向量检索系统 (`retrieve.py`)
- ✅ Chroma v0.4.0+ 集成（已迁移到新 API）
- ✅ 基于 Embedding 的语义搜索
- ✅ 支持 sentence-transformers（BGE 中文模型）
- ✅ 按类型过滤检索
- ✅ 按人物名称检索

#### 3. LLM 集成 (`llm.py`)
- ✅ 多提供商支持：OpenAI、Anthropic、Alibaba Qwen、DeepSeek
- ✅ 统一的 LLM 接口
- ✅ 环境变量配置（支持 API Key、Model、Base URL）
- ✅ 自定义端点支持（代理、本地部署）
- ✅ 灵活的创建工厂模式

#### 4. 创意建议生成 (`suggest.py`)
- ✅ 基于记忆的创意建议生成
- ✅ 结构化记忆处理
- ✅ 提示词模板系统
- ✅ 人物特定建议生成
- ✅ LLM 响应解析

#### 5. CLI 应用 (`app.py`)
- ✅ 命令行界面
- ✅ 子命令模式：init、add、search、suggest、list、export
- ✅ 自动 .env 加载
- ✅ 错误处理

#### 6. 环境配置
- ✅ `.env.example` 配置模板
- ✅ 支持多个 LLM 提供商配置
- ✅ 自动环境变量加载

### 🔧 技术栈

```
Python >= 3.9
├── chroma-db >= 0.4.0          (向量数据库)
├── sentence-transformers       (文本嵌入)
├── openai >= 0.27.0           (OpenAI API)
├── anthropic >= 0.7.0         (Anthropic API)
├── pyyaml >= 6.0              (配置)
├── python-dotenv >= 1.0.0     (环境变量)
└── loguru >= 0.7.0            (日志)
```

### 📁 项目结构

```
novel-assistant/
├── app.py                      # CLI 应用入口
├── memory.py                   # 记忆管理
├── retrieve.py                 # 向量检索
├── llm.py                      # LLM 集成
├── suggest.py                  # 建议生成
├── requirements.txt            # 依赖声明
├── .env.example               # 配置模板
└── data/
    ├── memories/              # 记忆存储
    ├── chroma_db/             # 向量数据库
    └── raw_notes/             # 原始笔记
```

### 🚀 快速开始

#### 1. 安装依赖
```bash
pip install -r requirements.txt
```

#### 2. 配置环境
```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

#### 3. 初始化数据目录
```bash
python app.py init
```

#### 4. 添加记忆
```bash
python app.py add "男主角是一个神秘的剑客，有着复杂的背景故事"
```

#### 5. 搜索记忆
```bash
python app.py search "男主角是谁"
```

#### 6. 生成建议
```bash
python app.py suggest "如何设计一个转折点来揭露男主的身份？"
```

#### 7. 列出所有记忆
```bash
python app.py list
```

#### 8. 导出记忆
```bash
python app.py export --output memories.json
```

### 🐛 已知问题和限制

- Qwen 自定义端点支持还需完善
- 向量嵌入模型硬编码为 BGE 中文模型
- 提示词模板目前使用默认值（可从文件加载）
- 没有数据库索引优化

### 🔄 最近修复

- ✅ 修复 Chroma 弃用 API 警告（迁移到 PersistentClient）
- ✅ 添加 .env 自动加载
- ✅ 添加环境变量模型配置支持
- ✅ 创建 .env.example 配置模板

### 📝 开发笔记

此版本是可用的初版基线，包含完整的核心功能。后续改进方向：

1. **UI/UX 改进**：Web 界面或更友好的 CLI
2. **性能优化**：数据库索引、缓存机制
3. **更多 LLM 提供商**：OpenRouter、Together.ai 等
4. **高级检索**：混合检索、re-ranking
5. **记忆管理增强**：分类、标签、关系图
6. **持久化改进**：支持 SQLite、PostgreSQL
7. **多语言支持**：嵌入模型配置、多语言提示词

### 📄 许可证

此项目遵循相关许可证。

---

**发布日期**: 2026-05-30  
**发布者**: @dongqinggu  
**提交哈希**: bcc14bfd20739e12cfc38e30041be2ba43ab742d
