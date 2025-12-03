"""
AtomAgent Streaming & Async Support
Streaming responses for better UX and async operations
"""
import asyncio
from typing import AsyncGenerator, Generator, Callable, Any, Optional
from functools import wraps
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from utils.logger import get_logger

logger = get_logger()


class StreamingHandler:
    """
    Handles streaming responses from LLM.
    Provides both sync and async interfaces.
    """
    
    def __init__(self, on_token: Callable[[str], None] = None,
                 on_complete: Callable[[str], None] = None,
                 on_error: Callable[[Exception], None] = None):
        self.on_token = on_token or (lambda x: None)
        self.on_complete = on_complete or (lambda x: None)
        self.on_error = on_error or (lambda x: None)
        self.buffer = []
        self.is_streaming = False
    
    def handle_token(self, token: str):
        """Handle incoming token"""
        self.buffer.append(token)
        self.on_token(token)
    
    def get_full_response(self) -> str:
        """Get complete response"""
        return "".join(self.buffer)
    
    def reset(self):
        """Reset handler state"""
        self.buffer = []
        self.is_streaming = False


async def stream_agent_response(agent, task: str, thread_id: str = "default",
                                on_token: Callable[[str], None] = None) -> str:
    """
    Stream agent response for better UX.
    
    Args:
        agent: LangGraph agent
        task: Task to execute
        thread_id: Thread ID for memory
        on_token: Callback for each token
    
    Returns:
        Complete response string
    
    Usage:
        async for chunk in stream_agent_response(agent, "write hello world"):
            print(chunk, end="", flush=True)
    """
    config = {"configurable": {"thread_id": thread_id}}
    full_response = []
    
    try:
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=task)]},
            config,
            version="v2"
        ):
            kind = event.get("event")
            
            if kind == "on_chat_model_stream":
                content = event.get("data", {}).get("chunk", {})
                if hasattr(content, "content") and content.content:
                    token = content.content
                    full_response.append(token)
                    if on_token:
                        on_token(token)
            
            elif kind == "on_tool_start":
                tool_name = event.get("name", "unknown")
                logger.debug(f"Tool started: {tool_name}")
            
            elif kind == "on_tool_end":
                tool_name = event.get("name", "unknown")
                logger.debug(f"Tool ended: {tool_name}")
    
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        raise
    
    return "".join(full_response)


def sync_stream_response(agent, task: str, thread_id: str = "default") -> Generator[str, None, None]:
    """
    Synchronous streaming generator.
    
    Usage:
        for chunk in sync_stream_response(agent, "write code"):
            print(chunk, end="")
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        for event in agent.stream(
            {"messages": [HumanMessage(content=task)]},
            config,
            stream_mode="messages"
        ):
            if isinstance(event, tuple) and len(event) == 2:
                message, metadata = event
                if hasattr(message, "content") and message.content:
                    yield message.content
    
    except Exception as e:
        logger.error(f"Sync streaming error: {e}")
        raise


class AsyncTaskRunner:
    """
    Runs agent tasks asynchronously with progress tracking.
    """
    
    def __init__(self):
        self.tasks = {}
        self.results = {}
        self.errors = {}
    
    async def run_task(self, task_id: str, coro: Any) -> Any:
        """Run a coroutine and track its progress"""
        self.tasks[task_id] = "running"
        
        try:
            result = await coro
            self.results[task_id] = result
            self.tasks[task_id] = "completed"
            return result
        except Exception as e:
            self.errors[task_id] = str(e)
            self.tasks[task_id] = "failed"
            raise
    
    def get_status(self, task_id: str) -> dict:
        """Get task status"""
        return {
            "status": self.tasks.get(task_id, "unknown"),
            "result": self.results.get(task_id),
            "error": self.errors.get(task_id)
        }
    
    async def run_parallel(self, tasks: dict) -> dict:
        """
        Run multiple tasks in parallel.
        
        Args:
            tasks: Dict of {task_id: coroutine}
        
        Returns:
            Dict of {task_id: result}
        """
        async def wrapped(task_id, coro):
            try:
                return task_id, await coro, None
            except Exception as e:
                return task_id, None, str(e)
        
        results = await asyncio.gather(
            *[wrapped(tid, coro) for tid, coro in tasks.items()],
            return_exceptions=True
        )
        
        return {
            tid: {"result": res, "error": err}
            for tid, res, err in results
        }


# Global async runner
_async_runner = AsyncTaskRunner()


def get_async_runner() -> AsyncTaskRunner:
    """Get global async runner"""
    return _async_runner


def run_async(coro):
    """
    Run async coroutine from sync context.
    
    Usage:
        result = run_async(some_async_function())
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, create task
            return asyncio.ensure_future(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(coro)


def async_to_sync(func):
    """
    Decorator to convert async function to sync.
    
    Usage:
        @async_to_sync
        async def my_async_func():
            ...
        
        # Can now call synchronously
        result = my_async_func()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return run_async(func(*args, **kwargs))
    return wrapper
