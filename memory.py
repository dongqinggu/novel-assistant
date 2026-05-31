"""Memory Management Module

Responsibilities:
- Add/update/delete memories
- Load/save JSON files
- Coordinate with vector database
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class MemoryType(Enum):
    """Memory type enumeration"""
    CHARACTER = "character"
    PLOT = "plot"
    CALLBACK = "callback"
    OUTLINE = "outline"
    SCENE = "scene"
    WORLDBUILDING = "worldbuilding"
    NOTE = "note"


@dataclass
class Memory:
    """Core Memory data structure"""
    type: str  # character, plot, callback, outline, scene, worldbuilding, note
    content: str
    name: Optional[str] = None  # For character memories
    title: Optional[str] = None  # For non-character types
    source: Optional[str] = None  # Original user input
    tags: Optional[List[str]] = None  # Tags for filtering
    status: Optional[str] = None  # confirmed, pending, draft
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    id: Optional[str] = None  # UUID for tracking
    
    def __post_init__(self):
        if self.id is None:
            from uuid import uuid4
            self.id = str(uuid4())
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        if self.tags is None:
            self.tags = []
        if self.status is None:
            self.status = "confirmed"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def get_display_title(self) -> str:
        """Get display title for UI"""
        if self.title:
            return self.title
        if self.name:
            return self.name
        # Fallback: first 30 chars of content
        return self.content[:30] + "..." if len(self.content) > 30 else self.content


class MemoryManager:
    """Manages memory storage and retrieval from JSON"""
    
    def __init__(self, data_dir: str = "./data/memories"):
        """Initialize memory manager
        
        Args:
            data_dir: Directory to store memory JSON files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memories: Dict[str, Memory] = {}
        self._load_all_memories()
    
    def _load_all_memories(self) -> None:
        """Load all memories from disk"""
        json_files = self.data_dir.glob("*.json")
        for file in json_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure backward compatibility for new fields
                    if 'tags' not in data:
                        data['tags'] = []
                    if 'title' not in data:
                        data['title'] = None
                    if 'status' not in data:
                        data['status'] = 'confirmed'
                    memory = Memory(**data)
                    self.memories[memory.id] = memory
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error loading {file}: {e}")
    
    def add_memory(self, memory: Memory) -> str:
        """Add a new memory
        
        Args:
            memory: Memory object to add
            
        Returns:
            Memory ID
        """
        self.memories[memory.id] = memory
        self._save_memory(memory)
        return memory.id
    
    def update_memory(self, memory_id: str, **kwargs) -> Optional[Memory]:
        """Update an existing memory
        
        Args:
            memory_id: ID of memory to update
            **kwargs: Fields to update
            
        Returns:
            Updated memory or None if not found
        """
        if memory_id not in self.memories:
            return None
        
        memory = self.memories[memory_id]
        for key, value in kwargs.items():
            if hasattr(memory, key):
                setattr(memory, key, value)
        
        memory.updated_at = datetime.now().isoformat()
        self._save_memory(memory)
        return memory
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            True if deleted, False if not found
        """
        if memory_id not in self.memories:
            return False
        
        memory = self.memories.pop(memory_id)
        file_path = self.data_dir / f"{memory_id}.json"
        if file_path.exists():
            file_path.unlink()
        return True
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a specific memory
        
        Args:
            memory_id: ID of memory
            
        Returns:
            Memory object or None if not found
        """
        return self.memories.get(memory_id)
    
    def get_all_memories(self) -> List[Memory]:
        """Get all memories
        
        Returns:
            List of all memories
        """
        return list(self.memories.values())
    
    def get_memories_by_type(self, memory_type: str) -> List[Memory]:
        """Get memories by type
        
        Args:
            memory_type: Type of memory (character, plot, callback)
            
        Returns:
            List of matching memories
        """
        return [m for m in self.memories.values() if m.type == memory_type]
    
    def get_memories_by_character(self, character_name: str) -> List[Memory]:
        """Get all memories related to a character
        
        Args:
            character_name: Name of character
            
        Returns:
            List of character memories
        """
        return [
            m for m in self.memories.values()
            if m.type == MemoryType.CHARACTER.value and m.name == character_name
        ]
    
    def _save_memory(self, memory: Memory) -> None:
        """Save memory to disk
        
        Args:
            memory: Memory object to save
        """
        file_path = self.data_dir / f"{memory.id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(memory.to_dict(), f, ensure_ascii=False, indent=2)
    
    def export_all(self, output_file: str) -> None:
        """Export all memories to a single file
        
        Args:
            output_file: Path to output JSON file
        """
        data = {
            "exported_at": datetime.now().isoformat(),
            "total_memories": len(self.memories),
            "memories": [m.to_dict() for m in self.memories.values()]
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_from_file(self, input_file: str) -> int:
        """Import memories from a file
        
        Args:
            input_file: Path to JSON file containing memories
            
        Returns:
            Number of memories imported
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        memories = data.get('memories', [])
        for mem_data in memories:
            try:
                memory = Memory(**mem_data)
                self.add_memory(memory)
                count += 1
            except TypeError as e:
                print(f"Error importing memory: {e}")
        
        return count
