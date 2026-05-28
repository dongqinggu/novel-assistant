#!/usr/bin/env python3
"""Main Application Entry Point

Simple CLI for novel assistant.
"""

import argparse
import sys
from pathlib import Path

from memory import MemoryManager, Memory, MemoryType
from retrieve import MemoryRetriever, VectorStore
from suggest import SuggestionGenerator, StructureProcessor
from llm import LLMFactory


def init_data_dir():
    """Initialize data directory structure"""
    Path("data/memories").mkdir(parents=True, exist_ok=True)
    Path("data/raw_notes").mkdir(parents=True, exist_ok=True)
    Path("data/chroma_db").mkdir(parents=True, exist_ok=True)
    print("✓ Data directories initialized")


def add_memory_command(args):
    """Add a new memory"""
    processor = StructureProcessor()
    
    print(f"Processing input: {args.input[:50]}...")
    memories = processor.process_input(args.input)
    
    print(f"✓ Added {len(memories)} memory/memories:")
    for mem in memories:
        print(f"  - [{mem.type}] {mem.content[:60]}...")


def search_command(args):
    """Search for memories"""
    retriever = MemoryRetriever()
    
    # Sync vector DB first
    print("Syncing memories to vector database...")
    retriever.sync_memories_to_vector_db()
    
    print(f"Searching: {args.query}")
    results = retriever.search_memories(args.query, n_results=args.limit or 5)
    
    if not results:
        print("No memories found.")
        return
    
    print(f"✓ Found {len(results)} memories:")
    for i, mem in enumerate(results, 1):
        print(f"  {i}. [{mem.type.upper()}] {mem.content}")


def suggest_command(args):
    """Generate writing suggestions"""
    suggester = SuggestionGenerator()
    
    print(f"Generating suggestions for: {args.context}")
    suggestions = suggester.generate_suggestions(args.context, n_suggestions=args.count or 5)
    
    if not suggestions:
        print("Could not generate suggestions.")
        return
    
    print(f"✓ Suggestions ({len(suggestions)}):")
    for i, sugg in enumerate(suggestions, 1):
        print(f"  {i}. {sugg}")


def list_memories_command(args):
    """List all memories"""
    manager = MemoryManager()
    memories = manager.get_all_memories()
    
    if not memories:
        print("No memories found.")
        return
    
    print(f"Total memories: {len(memories)}\n")
    
    # Group by type
    by_type = {}
    for mem in memories:
        if mem.type not in by_type:
            by_type[mem.type] = []
        by_type[mem.type].append(mem)
    
    for mem_type in ["character", "plot", "callback"]:
        if mem_type in by_type:
            print(f"\n【{mem_type.upper()}】")
            for mem in by_type[mem_type]:
                if mem.name:
                    print(f"  - {mem.name}: {mem.content}")
                else:
                    print(f"  - {mem.content}")


def export_command(args):
    """Export all memories"""
    manager = MemoryManager()
    output = args.output or "memories_export.json"
    
    manager.export_all(output)
    print(f"✓ Exported memories to {output}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI Novel Creation Memory Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize data directories")
    init_parser.set_defaults(func=lambda args: init_data_dir())
    
    # Add memory command
    add_parser = subparsers.add_parser("add", help="Add a new memory")
    add_parser.add_argument("input", help="Memory content")
    add_parser.set_defaults(func=add_memory_command)
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search memories")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=5, help="Number of results")
    search_parser.set_defaults(func=search_command)
    
    # Suggest command
    suggest_parser = subparsers.add_parser("suggest", help="Generate suggestions")
    suggest_parser.add_argument("context", help="Writing context")
    suggest_parser.add_argument("--count", type=int, default=5, help="Number of suggestions")
    suggest_parser.set_defaults(func=suggest_command)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all memories")
    list_parser.set_defaults(func=lambda args: list_memories_command(args))
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export memories")
    export_parser.add_argument("--output", help="Output file")
    export_parser.set_defaults(func=export_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
