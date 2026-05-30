"""FastAPI Web Application for Novel Assistant

Provides a web interface for the novel assistant system.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
from pathlib import Path

from memory import MemoryManager, Memory, MemoryType
from retrieve import MemoryRetriever
from suggest import SuggestionGenerator, StructureProcessor
from llm import LLMFactory

# Initialize FastAPI app
app = FastAPI(
    title="Novel Assistant",
    description="AI-powered creative writing assistant",
    version="0.1.0"
)

# Initialize managers
memory_manager = MemoryManager()
retriever = MemoryRetriever()
suggester = SuggestionGenerator()


# ============ Pydantic Models ============

class MemoryInput(BaseModel):
    """Input model for adding memories"""
    type: str  # character, plot, callback, outline, scene
    content: str
    name: Optional[str] = None


class MemoryResponse(BaseModel):
    """Output model for memories"""
    id: str
    type: str
    content: str
    name: Optional[str] = None
    created_at: str


class SearchRequest(BaseModel):
    """Request model for searching memories"""
    query: str
    memory_type: Optional[str] = None
    limit: int = 5


class SearchResponse(BaseModel):
    """Response model for search results"""
    results: List[MemoryResponse]
    count: int


class IdeaBoxInput(BaseModel):
    """Input model for idea box - creative spark"""
    idea: str  # User's creative idea
    search_query: Optional[str] = None  # What to search from memories
    memory_types: Optional[List[str]] = None  # Types to search


class SuggestionItem(BaseModel):
    """Single suggestion item"""
    text: str
    source_type: str  # from_ai, from_memory


class IdeaBoxResponse(BaseModel):
    """Response model for idea box processing"""
    original_idea: str
    retrieved_memories: List[MemoryResponse]
    ai_suggestions: List[str]
    formatted_idea: str  # Ready to submit as new memory


class ConfirmIdeaRequest(BaseModel):
    """Request to confirm and save formatted idea"""
    idea: str
    memory_type: str
    name: Optional[str] = None


class StatsResponse(BaseModel):
    """Statistics response"""
    total_memories: int
    by_type: Dict[str, int]
    memory_types_available: List[str]


# ============ API Routes ============

@app.get("/")
async def root():
    """Root endpoint - return index.html"""
    return FileResponse("static/index.html")


@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    memories = memory_manager.get_all_memories()
    by_type = {}
    for mem in memories:
        by_type[mem.type] = by_type.get(mem.type, 0) + 1
    
    return StatsResponse(
        total_memories=len(memories),
        by_type=by_type,
        memory_types_available=["character", "plot", "callback", "outline", "scene"]
    )


@app.get("/api/memories")
async def list_memories(memory_type: Optional[str] = None):
    """List all memories, optionally filtered by type"""
    if memory_type:
        memories = memory_manager.get_memories_by_type(memory_type)
    else:
        memories = memory_manager.get_all_memories()
    
    return {
        "memories": [
            MemoryResponse(
                id=m.id,
                type=m.type,
                content=m.content,
                name=m.name,
                created_at=m.created_at
            )
            for m in memories
        ],
        "total": len(memories)
    }


@app.post("/api/memories")
async def add_memory(memory: MemoryInput):
    """Add a new memory"""
    new_memory = Memory(
        type=memory.type,
        content=memory.content,
        name=memory.name
    )
    memory_id = memory_manager.add_memory(new_memory)
    
    # Sync to vector DB
    retriever.sync_memories_to_vector_db()
    
    return MemoryResponse(
        id=new_memory.id,
        type=new_memory.type,
        content=new_memory.content,
        name=new_memory.name,
        created_at=new_memory.created_at
    )


@app.delete("/api/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory"""
    success = memory_manager.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    retriever.sync_memories_to_vector_db()
    return {"deleted": memory_id}


@app.post("/api/search")
async def search_memories(request: SearchRequest):
    """Search for memories"""
    print(f"Syncing memories to vector database...")
    retriever.sync_memories_to_vector_db()
    
    if request.memory_type:
        results = retriever.search_by_type(request.query, request.memory_type, request.limit)
    else:
        results = retriever.search_memories(request.query, request.limit)
    
    return SearchResponse(
        results=[
            MemoryResponse(
                id=m.id,
                type=m.type,
                content=m.content,
                name=m.name,
                created_at=m.created_at
            )
            for m in results
        ],
        count=len(results)
    )


@app.post("/api/ideabox/process")
async def process_idea(request: IdeaBoxInput):
    """
    Process creative idea through the idea box:
    1. Retrieve related memories
    2. Get AI suggestions
    3. Format as structured idea
    """
    # Determine what to search
    search_query = request.search_query or request.idea
    
    # Search for related memories
    retriever.sync_memories_to_vector_db()
    
    related_memories = []
    if request.memory_types:
        for mem_type in request.memory_types:
            results = retriever.search_by_type(search_query, mem_type, n_results=3)
            related_memories.extend(results)
    else:
        related_memories = retriever.search_memories(search_query, n_results=5)
    
    # Format memories for display
    memory_responses = [
        MemoryResponse(
            id=m.id,
            type=m.type,
            content=m.content,
            name=m.name,
            created_at=m.created_at
        )
        for m in related_memories
    ]
    
    # Get AI suggestions
    try:
        suggestions = suggester.generate_suggestions(
            request.idea,
            n_suggestions=5
        )
    except Exception as e:
        print(f"Error generating suggestions: {e}")
        suggestions = [
            "Could not generate AI suggestions due to an error",
            "Try checking your LLM configuration"
        ]
    
    # Format idea with memories and suggestions
    formatted_idea = _format_idea(request.idea, related_memories, suggestions)
    
    return IdeaBoxResponse(
        original_idea=request.idea,
        retrieved_memories=memory_responses,
        ai_suggestions=suggestions,
        formatted_idea=formatted_idea
    )


@app.post("/api/ideabox/confirm")
async def confirm_idea(request: ConfirmIdeaRequest):
    """Confirm formatted idea and save to memories"""
    new_memory = Memory(
        type=request.memory_type,
        content=request.idea,
        name=request.name
    )
    memory_id = memory_manager.add_memory(new_memory)
    
    # Sync to vector DB
    retriever.sync_memories_to_vector_db()
    
    return {
        "status": "saved",
        "memory_id": memory_id,
        "memory": MemoryResponse(
            id=new_memory.id,
            type=new_memory.type,
            content=new_memory.content,
            name=new_memory.name,
            created_at=new_memory.created_at
        )
    }


@app.get("/api/memories/by-type/{memory_type}")
async def get_memories_by_type(memory_type: str):
    """Get all memories of a specific type"""
    memories = memory_manager.get_memories_by_type(memory_type)
    
    return {
        "type": memory_type,
        "memories": [
            MemoryResponse(
                id=m.id,
                type=m.type,
                content=m.content,
                name=m.name,
                created_at=m.created_at
            )
            for m in memories
        ],
        "total": len(memories)
    }


@app.get("/api/memories/character/{character_name}")
async def get_character_memories(character_name: str):
    """Get all memories for a specific character"""
    memories = memory_manager.get_memories_by_character(character_name)
    
    return {
        "character": character_name,
        "memories": [
            MemoryResponse(
                id=m.id,
                type=m.type,
                content=m.content,
                name=m.name,
                created_at=m.created_at
            )
            for m in memories
        ],
        "total": len(memories)
    }


@app.post("/api/export")
async def export_memories(output_file: str = "memories_export.json"):
    """Export all memories to JSON file"""
    memory_manager.export_all(output_file)
    return {
        "status": "exported",
        "file": output_file
    }


@app.post("/api/import")
async def import_memories(input_file: str):
    """Import memories from JSON file"""
    count = memory_manager.import_from_file(input_file)
    retriever.sync_memories_to_vector_db()
    return {
        "status": "imported",
        "count": count
    }


# ============ Helper Functions ============

def _format_idea(idea: str, memories: List[Memory], suggestions: List[str]) -> str:
    """Format idea with context from memories and suggestions"""
    formatted = f"""## 创意草稿

### 原始想法
{idea}

### 相关记忆
"""
    
    if memories:
        for mem in memories:
            formatted += f"\n- 【{mem.type.upper()}】"
            if mem.name:
                formatted += f" {mem.name}："
            formatted += f" {mem.content}"
    else:
        formatted += "\n（暂无相关记忆）"
    
    formatted += "\n\n### AI 建议\n"
    if suggestions:
        for i, suggestion in enumerate(suggestions, 1):
            formatted += f"{i}. {suggestion}\n"
    else:
        formatted += "（无建议）\n"
    
    formatted += "\n### 完善后的想法\n"
    formatted += f"{idea}\n"
    
    return formatted


# Mount static files directory
Path("static").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
