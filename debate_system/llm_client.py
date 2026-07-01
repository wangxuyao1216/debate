"""
LLM Client wrapper for interacting with DeepSeek API (OpenAI-compatible).
"""

import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI

from debate_system.config import Config

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Wrapper around the OpenAI-compatible LLM API.
    Supports both simple chat and tool-calling modes.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.client = OpenAI(
            api_key=self.config.LLM_API_KEY,
            base_url=self.config.LLM_BASE_URL,
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto",
    ) -> Dict[str, Any]:
        """
        Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature.
            max_tokens: Max tokens to generate.
            tools: Optional tool definitions for function calling.
            tool_choice: Tool choice mode ('auto', 'none', or specific).

        Returns:
            The API response as a dict.

        Raises:
            Exception: On API errors, with retry logic.
        """
        kwargs = {
            "model": self.config.LLM_MODEL,
            "messages": messages,
            "temperature": temperature or self.config.LLM_TEMPERATURE,
            "max_tokens": max_tokens or self.config.LLM_MAX_TOKENS,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(**kwargs)
                return response.model_dump()
            except Exception as e:
                logger.warning(
                    f"LLM API call failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt == max_retries - 1:
                    logger.error(f"LLM API call failed after {max_retries} retries")
                    raise
                import time

                time.sleep(2**attempt)

        raise RuntimeError("Unreachable")

    def chat_simple(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Send a chat request and return just the text content.

        Args:
            messages: Chat messages.
            **kwargs: Additional parameters for chat().

        Returns:
            The assistant's text response.
        """
        response = self.chat(messages, **kwargs)
        choice = response["choices"][0]
        content = choice["message"].get("content", "")
        return content or ""

    def get_tool_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tool calls from an API response.

        Args:
            response: The full API response dict.

        Returns:
            List of tool call dicts, each with 'name' and 'arguments'.
        """
        choice = response["choices"][0]
        message = choice["message"]
        tool_calls = message.get("tool_calls", [])
        result = []
        for tc in tool_calls:
            func = tc.get("function", {})
            import json

            args = {}
            try:
                args = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}
            result.append({"id": tc.get("id"), "name": func.get("name"), "arguments": args})
        return result

    def chat_with_tool_result(
        self,
        messages: List[Dict[str, str]],
        tool_call_id: str,
        tool_name: str,
        tool_result: str,
    ) -> str:
        """
        Continue a conversation after a tool call, returning the next text response.

        Args:
            messages: The conversation so far.
            tool_call_id: The ID of the tool call being responded to.
            tool_name: The name of the called tool.
            tool_result: The result returned by the tool.

        Returns:
            The assistant's follow-up text response.
        """
        # Append the assistant's tool call message
        assistant_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {"name": tool_name, "arguments": "{}"},
                }
            ],
        }
        # Append the tool result
        tool_msg = {"role": "tool", "tool_call_id": tool_call_id, "content": tool_result}

        messages_copy = list(messages) + [assistant_msg, tool_msg]
        return self.chat_simple(messages_copy)
