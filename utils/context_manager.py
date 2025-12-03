"""
AtomAgent Context Window Manager
Smart context compression and management for long conversations
"""
import tiktoken
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from utils.logger import get_logger

logger = get_logger()

# Default token limits for different models
MODEL_CONTEXT_LIMITS = {
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-3.5-turbo": 16385,
    "claude-3-5-sonnet": 200000,
    "claude-3-opus": 200000,
    "gemini-1.5-pro": 1000000,
    "gemini-1.5-flash": 1000000,
    "llama3.2": 8192,
    "llama3.1": 128000,
    "default": 8192
}


@dataclass
class ContextStats:
    """Statistics about context usage"""
    total_tokens: int
    message_count: int
    system_tokens: int
    human_tokens: int
    ai_tokens: int
    tool_tokens: int
    compression_ratio: float = 1.0


class ContextWindowManager:
    """
    Manages context window to prevent overflow.
    Implements smart compression strategies.
    """
    
    def __init__(self, model: str = "default", max_tokens: int = None, 
                 reserve_tokens: int = 4000):
        self.model = model
        self.max_tokens = max_tokens or MODEL_CONTEXT_LIMITS.get(
            model, MODEL_CONTEXT_LIMITS["default"]
        )
        self.reserve_tokens = reserve_tokens  # Reserve for response
        self.available_tokens = self.max_tokens - reserve_tokens
        
        # Try to load tiktoken, fallback to estimation
        try:
            self.encoder = tiktoken.encoding_for_model("gpt-4")
        except:
            self.encoder = None
            logger.warning("tiktoken not available, using estimation")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.encoder:
            return len(self.encoder.encode(text))
        # Fallback: estimate ~4 chars per token
        return len(text) // 4
    
    def count_message_tokens(self, message: BaseMessage) -> int:
        """Count tokens in a message"""
        content = message.content if isinstance(message.content, str) else str(message.content)
        # Add overhead for message structure
        return self.count_tokens(content) + 4
    
    def get_context_stats(self, messages: List[BaseMessage]) -> ContextStats:
        """Get detailed statistics about context usage"""
        system_tokens = 0
        human_tokens = 0
        ai_tokens = 0
        tool_tokens = 0
        
        for msg in messages:
            tokens = self.count_message_tokens(msg)
            
            if isinstance(msg, SystemMessage):
                system_tokens += tokens
            elif isinstance(msg, HumanMessage):
                human_tokens += tokens
            elif isinstance(msg, AIMessage):
                ai_tokens += tokens
                # Check for tool calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_tokens += tokens // 2
        
        return ContextStats(
            total_tokens=system_tokens + human_tokens + ai_tokens,
            message_count=len(messages),
            system_tokens=system_tokens,
            human_tokens=human_tokens,
            ai_tokens=ai_tokens,
            tool_tokens=tool_tokens
        )
    
    def needs_compression(self, messages: List[BaseMessage]) -> bool:
        """Check if context needs compression"""
        stats = self.get_context_stats(messages)
        return stats.total_tokens > self.available_tokens * 0.8
    
    def compress_context(self, messages: List[BaseMessage], 
                        target_ratio: float = 0.6) -> List[BaseMessage]:
        """
        Compress context to fit within limits.
        
        Strategies:
        1. Keep system message intact
        2. Keep last N messages intact
        3. Summarize older messages
        4. Truncate tool outputs
        """
        stats = self.get_context_stats(messages)
        
        if stats.total_tokens <= self.available_tokens:
            return messages
        
        target_tokens = int(self.available_tokens * target_ratio)
        logger.info(f"Compressing context: {stats.total_tokens} -> {target_tokens} tokens")
        
        compressed = []
        current_tokens = 0
        
        # 1. Always keep system message
        system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
        for msg in system_msgs:
            compressed.append(msg)
            current_tokens += self.count_message_tokens(msg)
        
        # 2. Keep last 5 messages intact
        recent_messages = [m for m in messages if not isinstance(m, SystemMessage)][-5:]
        recent_tokens = sum(self.count_message_tokens(m) for m in recent_messages)
        
        # 3. Process older messages
        older_messages = [m for m in messages if not isinstance(m, SystemMessage)][:-5]
        remaining_tokens = target_tokens - current_tokens - recent_tokens
        
        if older_messages and remaining_tokens > 0:
            # Summarize older messages
            summary = self._summarize_messages(older_messages, remaining_tokens)
            if summary:
                compressed.append(SystemMessage(content=f"[Previous conversation summary]\n{summary}"))
                current_tokens += self.count_tokens(summary)
        
        # 4. Add recent messages
        compressed.extend(recent_messages)
        
        final_stats = self.get_context_stats(compressed)
        logger.info(f"Compression complete: {len(messages)} -> {len(compressed)} messages, "
                   f"{stats.total_tokens} -> {final_stats.total_tokens} tokens")
        
        return compressed
    
    def _summarize_messages(self, messages: List[BaseMessage], 
                           max_tokens: int) -> Optional[str]:
        """Create a summary of messages"""
        if not messages:
            return None
        
        summary_parts = []
        
        for msg in messages:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            
            if isinstance(msg, HumanMessage):
                # Extract key points from user messages
                summary_parts.append(f"User asked: {content[:100]}...")
            elif isinstance(msg, AIMessage):
                # Extract key actions from AI messages
                if "created" in content.lower() or "wrote" in content.lower():
                    summary_parts.append(f"Agent created/modified files")
                elif "error" in content.lower():
                    summary_parts.append(f"Agent encountered an error")
                else:
                    summary_parts.append(f"Agent responded: {content[:50]}...")
        
        summary = "\n".join(summary_parts[:10])  # Max 10 summary points
        
        # Truncate if still too long
        while self.count_tokens(summary) > max_tokens and summary_parts:
            summary_parts.pop()
            summary = "\n".join(summary_parts)
        
        return summary
    
    def truncate_tool_output(self, output: str, max_tokens: int = 500) -> str:
        """Truncate tool output to save tokens"""
        if self.count_tokens(output) <= max_tokens:
            return output
        
        # Keep first and last parts
        lines = output.split('\n')
        if len(lines) <= 10:
            return output[:max_tokens * 4] + "\n...[truncated]..."
        
        # Keep first 5 and last 5 lines
        truncated = '\n'.join(lines[:5]) + '\n...[truncated]...\n' + '\n'.join(lines[-5:])
        return truncated
    
    def optimize_for_model(self, messages: List[BaseMessage], 
                          model: str = None) -> List[BaseMessage]:
        """Optimize context for specific model"""
        model = model or self.model
        limit = MODEL_CONTEXT_LIMITS.get(model, MODEL_CONTEXT_LIMITS["default"])
        
        # Update limits for this optimization
        old_max = self.max_tokens
        self.max_tokens = limit
        self.available_tokens = limit - self.reserve_tokens
        
        result = self.compress_context(messages) if self.needs_compression(messages) else messages
        
        # Restore original limits
        self.max_tokens = old_max
        self.available_tokens = old_max - self.reserve_tokens
        
        return result


# Global context manager
_context_manager = None


def get_context_manager(model: str = "default") -> ContextWindowManager:
    """Get or create context manager"""
    global _context_manager
    if _context_manager is None or _context_manager.model != model:
        _context_manager = ContextWindowManager(model)
    return _context_manager


def smart_context_compression(messages: List[BaseMessage], 
                             max_tokens: int = 8000) -> List[BaseMessage]:
    """
    Convenience function for context compression.
    
    Args:
        messages: List of messages to compress
        max_tokens: Target maximum tokens
    
    Returns:
        Compressed message list
    """
    manager = ContextWindowManager(max_tokens=max_tokens + 4000)
    return manager.compress_context(messages)
