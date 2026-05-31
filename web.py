#!/usr/bin/env python3
"""FastAPI Web Application for Novel Assistant

Web interface for the novel creation memory assistant.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from dotenv import load_dotenv

from memory import Memory, MemoryManager, MemoryType
from suggest import SuggestionGenerator

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="创意工坊")

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "css").mkdir(exist_ok=True)
(STATIC_DIR / "js").mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates - use jinja2 directly to avoid Starlette compatibility issues
from jinja2 import Environment, FileSystemLoader
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)

# Add global functions to Jinja2 (registered after helper functions are defined)
# See below after get_type_display_name / get_type_icon definitions


def render_template(template_name: str, **context) -> str:
    """Render a Jinja2 template with context"""
    template = jinja_env.get_template(template_name)
    return template.render(**context)


def template_response(template_name: str, request: Request, **context) -> HTMLResponse:
    """Create an HTMLResponse from a Jinja2 template"""
    context["request"] = request
    html = render_template(template_name, **context)
    return HTMLResponse(content=html)

# Initialize managers (with graceful error handling)
memory_manager = MemoryManager()
retriever = None
suggester = None
vector_db_available = False

try:
    from retrieve import MemoryRetriever
    retriever = MemoryRetriever(memory_manager=memory_manager)
    vector_db_available = True
except ImportError as e:
    print(f"Warning: Vector DB not available: {e}")
    print("Memory search will be disabled. Install chromadb to enable.")

try:
    suggester = SuggestionGenerator()
except Exception as e:
    print(f"Warning: Suggestion generator not available: {e}")
    print("AI suggestions will be disabled. Check LLM configuration.")


# ============ Pydantic Models ============

class MemoryCreate(BaseModel):
    type: str
    content: str
    title: Optional[str] = None
    name: Optional[str] = None
    tags: List[str] = []
    source: Optional[str] = None


class MemoryUpdate(BaseModel):
    type: Optional[str] = None
    content: Optional[str] = None
    title: Optional[str] = None
    name: Optional[str] = None
    tags: Optional[List[str]] = None


class InspirationSearch(BaseModel):
    query: str
    type: str = "auto"


class InspirationAdvise(BaseModel):
    query: str
    related_memories: List[Dict[str, Any]] = []
    memory_type: str = "auto"


class ConfirmMemories(BaseModel):
    memories: List[MemoryCreate]


class FormatIdea(BaseModel):
    content: str
    memory_type: str = "auto"


# ============ Helper Functions ============

def get_type_display_name(type_val: str) -> str:
    """Get display name for memory type"""
    type_names = {
        "outline": "大纲",
        "character": "人物",
        "scene": "场景",
        "plot": "剧情",
        "callback": "伏笔",
        "worldbuilding": "世界观",
        "note": "笔记",
    }
    return type_names.get(type_val, type_val)


def get_type_icon(type_val: str) -> str:
    """Get icon for memory type"""
    type_icons = {
        "outline": "📋",
        "character": "👤",
        "scene": "📍",
        "plot": "📖",
        "callback": "🔗",
        "worldbuilding": "🌍",
        "note": "📝",
    }
    return type_icons.get(type_val, "📄")


# Register global functions to Jinja2 (must be after function definitions)
jinja_env.globals['getTypeName'] = get_type_display_name
jinja_env.globals['getTypeIcon'] = get_type_icon
jinja_env.globals['formatDate'] = lambda d: d[:10] if d else ''


def format_memory_for_display(memory: Memory) -> Dict[str, Any]:
    """Format memory for display in templates"""
    return {
        "id": memory.id,
        "type": memory.type,
        "type_display": get_type_display_name(memory.type),
        "type_icon": get_type_icon(memory.type),
        "title": memory.get_display_title(),
        "content": memory.content,
        "name": memory.name,
        "tags": memory.tags or [],
        "status": memory.status,
        "created_at": memory.created_at,
        "updated_at": memory.updated_at,
    }


def get_stats() -> Dict[str, Any]:
    """Get memory statistics"""
    all_memories = memory_manager.get_all_memories()
    
    by_type = {}
    for mem in all_memories:
        by_type[mem.type] = by_type.get(mem.type, 0) + 1
    
    return {
        "total": len(all_memories),
        "by_type": by_type,
    }


# ============ Page Routes ============

@app.get("/", response_class=HTMLResponse)
async def page_inspiration(request: Request):
    """Inspiration box - Home page"""
    stats = get_stats()
    return template_response(
        "inspiration.html",
        request,
        page="inspiration",
        stats=stats,
    )


@app.get("/outline", response_class=HTMLResponse)
async def page_outline(request: Request):
    """Outline page"""
    memories = memory_manager.get_memories_by_type("outline")
    stats = get_stats()
    return template_response(
        "list.html",
        request,
        page="outline",
        page_title="大纲",
        memories=[format_memory_for_display(m) for m in memories],
        stats=stats,
    )


@app.get("/character", response_class=HTMLResponse)
async def page_character(request: Request):
    """Character page"""
    memories = memory_manager.get_memories_by_type("character")
    
    # Group by character name
    characters = {}
    for mem in memories:
        name = mem.name or "未命名"
        if name not in characters:
            characters[name] = []
        characters[name].append(format_memory_for_display(mem))
    
    stats = get_stats()
    return template_response(
        "character.html",
        request,
        page="character",
        page_title="人物",
        characters=characters,
        stats=stats,
    )


@app.get("/scene", response_class=HTMLResponse)
async def page_scene(request: Request):
    """Scene page"""
    memories = memory_manager.get_memories_by_type("scene")
    stats = get_stats()
    return template_response(
        "cards.html",
        request,
        page="scene",
        page_title="场景",
        memories=[format_memory_for_display(m) for m in memories],
        stats=stats,
    )


@app.get("/plot", response_class=HTMLResponse)
async def page_plot(request: Request):
    """Plot page"""
    memories = memory_manager.get_memories_by_type("plot")
    stats = get_stats()
    return template_response(
        "list.html",
        request,
        page="plot",
        page_title="剧情",
        memories=[format_memory_for_display(m) for m in memories],
        stats=stats,
    )


@app.get("/callback", response_class=HTMLResponse)
async def page_callback(request: Request):
    """Callback/Foreshadowing page"""
    memories = memory_manager.get_memories_by_type("callback")
    stats = get_stats()
    return template_response(
        "list.html",
        request,
        page="callback",
        page_title="伏笔",
        memories=[format_memory_for_display(m) for m in memories],
        stats=stats,
    )


@app.get("/worldbuilding", response_class=HTMLResponse)
async def page_worldbuilding(request: Request):
    """Worldbuilding page"""
    memories = memory_manager.get_memories_by_type("worldbuilding")
    stats = get_stats()
    return template_response(
        "cards.html",
        request,
        page="worldbuilding",
        page_title="世界观",
        memories=[format_memory_for_display(m) for m in memories],
        stats=stats,
    )


@app.get("/memories", response_class=HTMLResponse)
async def page_memories(
    request: Request,
    type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """All memories page"""
    memories = memory_manager.get_all_memories()
    
    # Filter by type
    if type and type != "all":
        memories = [m for m in memories if m.type == type]
    
    # Filter by search
    if search:
        search_lower = search.lower()
        memories = [
            m for m in memories
            if search_lower in m.content.lower()
            or (m.title and search_lower in m.title.lower())
            or (m.name and search_lower in m.name.lower())
        ]
    
    stats = get_stats()
    return template_response(
        "memories.html",
        request,
        page="memories",
        page_title="全部记忆",
        memories=[format_memory_for_display(m) for m in memories],
        stats=stats,
        current_type=type or "all",
        search_query=search or "",
    )


@app.get("/entity/{entity_id}", response_class=HTMLResponse)
async def page_entity_detail(request: Request, entity_id: str):
    """Entity detail page - works for all memory types"""
    entity = memory_manager.get_memory(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Get related memories using vector search
    related_memories = []
    if retriever:
        try:
            search_query = entity.content
            if entity.name:
                search_query = entity.name + " " + search_query
            related = retriever.search_memories(search_query, n_results=6)
            # Filter out the entity itself
            related_memories = [
                format_memory_for_display(m) for m in related 
                if m.id != entity_id
            ][:5]
        except Exception as e:
            print(f"Error searching related: {e}")
    
    # Get other entities of same type
    other_entities = [
        format_memory_for_display(m) 
        for m in memory_manager.get_memories_by_type(entity.type)
        if m.id != entity_id
    ][:5]
    
    stats = get_stats()
    return template_response(
        "entity_detail.html",
        request,
        page=entity.type,
        entity_title=get_type_display_name(entity.type),
        entity=format_memory_for_display(entity),
        related_memories=related_memories,
        other_entities=other_entities,
        stats=stats,
    )


# ============ API Routes ============

@app.get("/api/memories")
async def api_get_memories(
    type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """Get memories list"""
    memories = memory_manager.get_all_memories()
    
    if type and type != "all":
        memories = [m for m in memories if m.type == type]
    
    if search:
        search_lower = search.lower()
        memories = [
            m for m in memories
            if search_lower in m.content.lower()
            or (m.title and search_lower in m.title.lower())
        ]
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "memories": [format_memory_for_display(m) for m in memories],
            "total": len(memories),
        }
    }


@app.get("/api/memories/{memory_id}")
async def api_get_memory(memory_id: str):
    """Get single memory"""
    memory = memory_manager.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {
        "code": 0,
        "message": "success",
        "data": format_memory_for_display(memory),
    }


@app.post("/api/memories")
async def api_create_memory(memory_data: MemoryCreate):
    """Create new memory"""
    memory = Memory(
        type=memory_data.type,
        content=memory_data.content,
        title=memory_data.title,
        name=memory_data.name,
        tags=memory_data.tags,
        source=memory_data.source,
    )
    
    memory_id = memory_manager.add_memory(memory)
    
    # Sync to vector DB
    if retriever:
        try:
            retriever.vector_store.add_memory(memory)
        except Exception as e:
            print(f"Warning: Could not sync to vector DB: {e}")
    
    return {
        "code": 0,
        "message": "Memory created successfully",
        "data": {"id": memory_id},
    }


@app.put("/api/memories/{memory_id}")
async def api_update_memory(memory_id: str, memory_data: MemoryUpdate):
    """Update memory"""
    update_kwargs = memory_data.dict(exclude_unset=True)
    
    memory = memory_manager.update_memory(memory_id, **update_kwargs)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Sync to vector DB
    if retriever:
        try:
            retriever.vector_store.update_memory(memory)
        except Exception as e:
            print(f"Warning: Could not sync to vector DB: {e}")
    
    return {
        "code": 0,
        "message": "Memory updated successfully",
        "data": format_memory_for_display(memory),
    }


@app.delete("/api/memories/{memory_id}")
async def api_delete_memory(memory_id: str):
    """Delete memory"""
    success = memory_manager.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Delete from vector DB
    if retriever:
        try:
            retriever.vector_store.delete_memory(memory_id)
        except Exception as e:
            print(f"Warning: Could not delete from vector DB: {e}")
    
    return {
        "code": 0,
        "message": "Memory deleted successfully",
        "data": None,
    }


@app.post("/api/inspirations/search")
async def api_inspiration_search(data: InspirationSearch):
    """Search related memories for inspiration"""
    if not retriever:
        return {
            "code": 1,
            "message": "向量库未初始化，请安装 chromadb",
            "data": {"memories": []}
        }
    
    try:
        # Sync vector DB first
        retriever.sync_memories_to_vector_db()
        
        # Search
        memories = retriever.search_memories(data.query, n_results=10)
        
        return {
            "code": 0,
            "message": "success",
            "data": {
                "memories": [format_memory_for_display(m) for m in memories],
            }
        }
    except Exception as e:
        return {
            "code": 1,
            "message": f"Search failed: {str(e)}",
            "data": {"memories": []}
        }


@app.post("/api/inspirations/advise")
async def api_inspiration_advise(data: InspirationAdvise):
    """Generate suggestions and candidate memories"""
    if not suggester:
        return {
            "code": 1,
            "message": "AI 建议生成器未初始化，请检查 LLM 配置",
            "data": {
                "suggestions": [],
                "candidate_memories": [],
            }
        }
    
    try:
        # Get related memories
        related_memories = []
        if data.related_memories:
            for mem_data in data.related_memories:
                if "id" in mem_data:
                    mem = memory_manager.get_memory(mem_data["id"])
                    if mem:
                        related_memories.append(mem)
        
        # Generate advise
        result = suggester.generate_advise(
            query=data.query,
            related_memories=related_memories,
            memory_type=data.memory_type,
        )
        
        return {
            "code": 0,
            "message": "success",
            "data": result,
        }
    except Exception as e:
        return {
            "code": 1,
            "message": f"Failed to generate advise: {str(e)}",
            "data": {
                "suggestions": [],
                "candidate_memories": [],
            }
        }


@app.post("/api/inspirations/confirm")
async def api_inspiration_confirm(data: ConfirmMemories):
    """Confirm and save candidate memories"""
    saved_ids = []
    
    for mem_data in data.memories:
        memory = Memory(
            type=mem_data.type,
            content=mem_data.content,
            title=mem_data.title,
            name=mem_data.name,
            tags=mem_data.tags,
        )
        
        memory_id = memory_manager.add_memory(memory)
        saved_ids.append(memory_id)
        
        # Sync to vector DB
        if retriever:
            try:
                retriever.vector_store.add_memory(memory)
            except Exception as e:
                print(f"Warning: Could not sync to vector DB: {e}")
    
    return {
        "code": 0,
        "message": f"Saved {len(saved_ids)} memories",
        "data": {
            "saved": len(saved_ids),
            "ids": saved_ids,
        }
    }


@app.post("/api/vector/sync")
async def api_vector_sync():
    """Sync all memories to vector database"""
    if not retriever:
        return {
            "code": 1,
            "message": "向量库未初始化，请安装 chromadb",
            "data": None,
        }
    
    try:
        retriever.sync_memories_to_vector_db()
        return {
            "code": 0,
            "message": "Vector database synced successfully",
            "data": None,
        }
    except Exception as e:
        return {
            "code": 1,
            "message": f"Sync failed: {str(e)}",
            "data": None,
        }


@app.post("/api/ideas/format")
async def api_format_idea(data: FormatIdea):
    """Format raw idea into structured memories using AI"""
    if not suggester:
        return {
            "code": 1,
            "message": "AI 格式化服务未初始化，请检查 LLM 配置",
            "data": {"memories": []}
        }
    
    try:
        # Build prompt for formatting
        type_hint = f"目标类型：{data.memory_type}" if data.memory_type != "auto" else "自动判断类型"
        
        prompt = f"""你是一个小说创作记忆整理助手。

用户输入了一段原始构思，请将其整理成结构化的记忆条目。

用户构思：
{data.content}

{type_hint}

请分析这段构思，提取关键信息，整理成以下格式的 JSON：
{{
  "memories": [
    {{
      "type": "outline|character|scene|plot|callback|worldbuilding|note",
      "title": "标题（简洁明了）",
      "name": "人物名（仅character类型需要）",
      "content": "详细内容",
      "tags": ["标签1", "标签2"]
    }}
  ]
}}

要求：
1. 根据构思内容自动判断合适的类型
2. 如果构思包含多个元素（如人物+场景），可以返回多条记忆
3. title 要简洁，content 要详细
4. tags 用于分类和检索，3-5个为宜
5. 只输出 JSON，不要其他文本
"""
        
        # Call LLM
        response = suggester.llm.call(prompt)
        
        # Parse response
        import json
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                memories = result.get('memories', [])
            else:
                memories = []
        except json.JSONDecodeError:
            # Fallback: create a single note memory
            memories = [{
                'type': 'note',
                'title': data.content[:30] if len(data.content) > 30 else data.content,
                'content': data.content,
                'tags': [],
            }]
        
        return {
            "code": 0,
            "message": f"已格式化 {len(memories)} 条记忆",
            "data": {
                "memories": memories,
            }
        }
    except Exception as e:
        return {
            "code": 1,
            "message": f"格式化失败: {str(e)}",
            "data": {"memories": []}
        }


@app.post("/api/memories/link")
async def api_link_memories(data: dict):
    """Link memories together (create relationships)"""
    source_id = data.get('source_id')
    target_ids = data.get('target_ids', [])
    
    if not source_id or not target_ids:
        return {
            "code": 1,
            "message": "source_id and target_ids are required",
            "data": None,
        }
    
    try:
        # Add relationship info to memory content
        source = memory_manager.get_memory(source_id)
        if source:
            # Add a note about the relationship
            related_names = []
            for tid in target_ids:
                target = memory_manager.get_memory(tid)
                if target:
                    name = target.name or target.title or tid[:8]
                    related_names.append(f"{getTypeName(target.type)}:{name}")
            
            if related_names:
                relationship_note = f"\n\n[关联: {', '.join(related_names)}]"
                if relationship_note not in source.content:
                    source.content += relationship_note
                    memory_manager.update_memory(source_id, content=source.content)
        
        return {
            "code": 0,
            "message": f"Linked {len(target_ids)} memories",
            "data": {"linked": len(target_ids)},
        }
    except Exception as e:
        return {
            "code": 1,
            "message": f"Link failed: {str(e)}",
            "data": None,
        }


@app.post("/api/inspirations/process")
async def api_process_inspiration(data: dict):
    """
    Process inspiration in inspiration box:
    1. Format the idea
    2. Match with local entities
    3. Return formatted memories + matched entities
    """
    content = data.get('content', '')
    memory_type = data.get('memory_type', 'auto')
    
    if not content:
        return {
            "code": 1,
            "message": "Content is required",
            "data": None,
        }
    
    try:
        # 1. Format the idea using AI
        formatted_memories = []
        if suggester:
            type_hint = f"目标类型：{memory_type}" if memory_type != "auto" else "自动判断类型"
            prompt = f"""你是一个小说创作记忆整理助手。

用户输入了一段原始构思，请将其整理成结构化的记忆条目。

用户构思：
{content}

{type_hint}

请分析这段构思，提取关键信息，整理成以下格式的 JSON：
{{
  "memories": [
    {{
      "type": "outline|character|scene|plot|callback|worldbuilding|note",
      "title": "标题（简洁明了）",
      "name": "人物名（仅character类型需要）",
      "content": "详细内容",
      "tags": ["标签1", "标签2"]
    }}
  ]
}}

要求：
1. 根据构思内容自动判断合适的类型
2. 如果构思包含多个元素（如人物+场景），可以返回多条记忆
3. title 要简洁，content 要详细
4. tags 用于分类和检索，3-5个为宜
5. 只输出 JSON，不要其他文本
"""
            response = suggester.llm.call(prompt)
            try:
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                    result = json.loads(json_str)
                    formatted_memories = result.get('memories', [])
            except:
                formatted_memories = [{
                    'type': memory_type if memory_type != 'auto' else 'note',
                    'title': content[:30],
                    'content': content,
                    'tags': [],
                }]
        
        # 2. Search for matching entities
        matched_entities = []
        if retriever:
            try:
                retriever.sync_memories_to_vector_db()
                search_results = retriever.search_memories(content, n_results=10)
                matched_entities = [
                    format_memory_for_display(m) for m in search_results
                ]
            except Exception as e:
                print(f"Search error: {e}")
        
        return {
            "code": 0,
            "message": f"Formatted {len(formatted_memories)} memories, found {len(matched_entities)} matches",
            "data": {
                "formatted_memories": formatted_memories,
                "matched_entities": matched_entities,
            }
        }
    except Exception as e:
        return {
            "code": 1,
            "message": f"Processing failed: {str(e)}",
            "data": None,
        }


@app.get("/api/stats")
async def api_stats():
    """Get memory statistics"""
    return {
        "code": 0,
        "message": "success",
        "data": get_stats(),
    }


@app.get("/api/export")
async def api_export():
    """Export all memories"""
    memories = memory_manager.get_all_memories()
    return {
        "code": 0,
        "message": "success",
        "data": {
            "exported_at": datetime.now().isoformat(),
            "total": len(memories),
            "memories": [m.to_dict() for m in memories],
        }
    }


# ============ Run ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
