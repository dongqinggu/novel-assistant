"""Suggestion Generation Module

Generates creative suggestions based on retrieved memories.
"""

from typing import List, Optional, Dict
import json

from memory import Memory, MemoryManager
from retrieve import MemoryRetriever
from llm import LLMFactory, BaseLLM


class SuggestionGenerator:
    """Generates creative suggestions based on memories"""
    
    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        retriever: Optional[MemoryRetriever] = None,
        suggest_prompt_file: str = "prompts/suggest_prompt.txt",
    ):
        """Initialize suggestion generator
        
        Args:
            llm: LLM instance (uses default from env if not provided)
            retriever: MemoryRetriever instance
            suggest_prompt_file: Path to suggestion prompt template
        """
        self.llm = llm or LLMFactory.from_env()
        self.retriever = retriever or MemoryRetriever()
        self.suggest_prompt_template = self._load_prompt(suggest_prompt_file)
    
    def _load_prompt(self, prompt_file: str) -> str:
        """Load prompt template from file
        
        Args:
            prompt_file: Path to prompt file
            
        Returns:
            Prompt template
        """
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Return default prompt if file not found
            return """
你是一个小说创作助手。

你的职责是基于已有的创作记忆给出创作建议。

重要原则：
1. 基于已有记忆：只使用提供的记忆信息
2. 保持一致性：建议不能与已有设定矛盾
3. 不替代作者：提供可能性，而非结论
4. 启发性：帮助作者思考，而非限制想象

---

当前创作上下文：
{current_context}

相关记忆：
{retrieved_memories}

请基于以上信息，给出3-5条创作建议。

建议应该：
- 与现有设定保持一致
- 有具体的可操作性
- 开放而非强制
- 简洁而有启发性
"""
    
    def generate_suggestions(
        self,
        context: str,
        n_suggestions: int = 5,
    ) -> List[str]:
        """Generate suggestions for current writing context
        
        Args:
            context: Current writing context/question
            n_suggestions: Number of suggestions to generate
            
        Returns:
            List of suggestions
        """
        # Retrieve relevant memories
        memories = self.retriever.search_memories(context, n_results=5)
        
        # Format memories for prompt
        memories_text = self._format_memories(memories)
        
        # Fill prompt template
        prompt = self.suggest_prompt_template.format(
            current_context=context,
            retrieved_memories=memories_text
        )
        
        # Call LLM
        response = self.llm.call(prompt)
        
        # Parse response (simple parsing - can be improved)
        suggestions = self._parse_suggestions(response)
        
        return suggestions[:n_suggestions]
    
    def generate_suggestions_with_character(
        self,
        character_name: str,
        context: str,
        n_suggestions: int = 5,
    ) -> List[str]:
        """Generate suggestions for a specific character
        
        Args:
            character_name: Name of character
            context: Current writing context
            n_suggestions: Number of suggestions
            
        Returns:
            List of suggestions
        """
        # Retrieve character-specific memories
        memories = self.retriever.search_by_character(context, character_name, n_results=5)
        
        # Format memories
        memories_text = self._format_memories(memories)
        
        # Enhanced context
        enhanced_context = f"人物：{character_name}\n问题：{context}"
        
        # Fill prompt
        prompt = self.suggest_prompt_template.format(
            current_context=enhanced_context,
            retrieved_memories=memories_text
        )
        
        # Call LLM
        response = self.llm.call(prompt)
        suggestions = self._parse_suggestions(response)
        
        return suggestions[:n_suggestions]
    
    def _format_memories(self, memories: List[Memory]) -> str:
        """Format memories for prompt
        
        Args:
            memories: List of Memory objects
            
        Returns:
            Formatted memories text
        """
        if not memories:
            return "（暂无相关记忆）"
        
        lines = []
        for memory in memories:
            if memory.type == "character":
                line = f"【人物】{memory.name}: {memory.content}"
            elif memory.type == "plot":
                line = f"【剧情】{memory.content}"
            elif memory.type == "callback":
                line = f"【伏笔】{memory.content}"
            else:
                line = f"{memory.content}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def _parse_suggestions(self, response: str) -> List[str]:
        """Parse LLM response into suggestions
        
        Args:
            response: LLM response text
            
        Returns:
            List of suggestions
        """
        # Simple parsing: split by newlines and filter
        suggestions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and len(line) > 5:  # Filter empty and too short lines
                # Remove numbering if present
                if line[0].isdigit() and '.' in line[:3]:
                    line = line[line.index('.')+1:].strip()
                if line:
                    suggestions.append(line)
        
        return suggestions
    
    def generate_advise(
        self,
        query: str,
        related_memories: List[Memory],
        memory_type: str = "auto",
    ) -> Dict:
        """Generate suggestions and candidate memories for inspiration box
        
        Args:
            query: User's creative input/idea
            related_memories: List of retrieved related memories
            memory_type: Target memory type (auto/outline/character/scene/plot/callback/worldbuilding/note)
            
        Returns:
            Dict with 'suggestions' and 'candidate_memories'
        """
        # Format memories for prompt
        memories_text = self._format_memories(related_memories)
        
        # Build prompt
        type_hint = f"目标类型：{memory_type}" if memory_type != "auto" else "自动判断类型"
        
        prompt = f"""你是一个小说创作记忆助手。

用户输入了一个创作构思，请基于已有记忆给出建议，并整理成结构化的候选记忆。

已有相关记忆：
{memories_text}

用户构思：
{query}

{type_hint}

请输出 JSON 格式：
{{
  "suggestions": ["建议1", "建议2", ...],
  "candidate_memories": [
    {{
      "type": "character|plot|callback|outline|scene|worldbuilding|note",
      "title": "标题（character类型用name字段）",
      "name": "人物名（仅character类型）",
      "content": "核心内容",
      "tags": ["标签1", "标签2"]
    }}
  ]
}}

要求：
1. suggestions 给出 3-5 条创作建议，开放而非强制
2. candidate_memories 整理 1-3 条候选记忆
3. 保持与已有记忆的一致性
4. 只输出 JSON，不要其他文本
"""
        
        # Call LLM
        response = self.llm.call(prompt)
        
        # Parse response
        return self._parse_advise_response(response, query)
    
    def _parse_advise_response(self, response: str, original_query: str) -> Dict:
        """Parse AI response for inspiration advise
        
        Args:
            response: LLM response
            original_query: Original user query
            
        Returns:
            Dict with suggestions and candidate_memories
        """
        result = {
            "suggestions": [],
            "candidate_memories": []
        }
        
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                
                # Extract suggestions
                if 'suggestions' in data:
                    result['suggestions'] = data['suggestions']
                
                # Extract candidate memories
                if 'candidate_memories' in data:
                    for item in data['candidate_memories']:
                        if isinstance(item, dict):
                            candidate = {
                                'type': item.get('type', 'note'),
                                'title': item.get('title'),
                                'name': item.get('name'),
                                'content': item.get('content', ''),
                                'tags': item.get('tags', []),
                            }
                            # For character type, use name as title
                            if candidate['type'] == 'character' and candidate.get('name'):
                                candidate['title'] = candidate['name']
                            result['candidate_memories'].append(candidate)
        except json.JSONDecodeError:
            # Fallback: treat entire response as suggestions
            lines = [l.strip() for l in response.split('\n') if l.strip() and len(l.strip()) > 5]
            result['suggestions'] = lines[:5]
        
        return result


class StructureProcessor:
    """Processes user input into structured memories"""
    
    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        memory_manager: Optional[MemoryManager] = None,
        structure_prompt_file: str = "prompts/structure_prompt.txt",
    ):
        """Initialize structure processor
        
        Args:
            llm: LLM instance
            memory_manager: MemoryManager instance
            structure_prompt_file: Path to structure prompt template
        """
        self.llm = llm or LLMFactory.from_env()
        self.memory_manager = memory_manager or MemoryManager()
        self.structure_prompt_template = self._load_prompt(structure_prompt_file)
    
    def _load_prompt(self, prompt_file: str) -> str:
        """Load prompt template from file
        
        Args:
            prompt_file: Path to prompt file
            
        Returns:
            Prompt template
        """
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "Please structure this creative input: {input_text}"
    
    def process_input(self, user_input: str) -> List[Memory]:
        """Process user input into structured memories
        
        Args:
            user_input: Free-form user input
            
        Returns:
            List of Memory objects
        """
        # Fill prompt
        prompt = self.structure_prompt_template.format(input_text=user_input)
        
        # Call LLM
        response = self.llm.call(prompt)
        
        # Parse JSON response
        memories = self._parse_response(response, user_input)
        
        # Save memories
        for memory in memories:
            self.memory_manager.add_memory(memory)
        
        return memories
    
    def _parse_response(self, response: str, user_input: str) -> List[Memory]:
        """Parse LLM response into Memory objects
        
        Args:
            response: LLM response
            user_input: Original user input
            
        Returns:
            List of Memory objects
        """
        from memory import Memory
        
        memories = []
        
        # Try to extract JSON from response
        try:
            # Look for JSON array in response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                
                # Handle both single dict and list of dicts
                if isinstance(data, dict):
                    data = [data]
                
                for item in data:
                    if isinstance(item, dict):
                        memory = Memory(
                            type=item.get('type', 'plot'),
                            content=item.get('content', ''),
                            name=item.get('name'),
                            title=item.get('title'),
                            tags=item.get('tags', []),
                            source=user_input[:100]  # Store first 100 chars as source
                        )
                        if memory.content:
                            memories.append(memory)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a default memory from input
            memory = Memory(
                type="note",
                content=user_input,
                title=user_input[:30] if len(user_input) > 30 else user_input,
                source=user_input[:100]
            )
            memories.append(memory)
        
        return memories
