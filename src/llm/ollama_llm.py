# rag_system\llm\ollama_llm.py
from llama_index.core.llms import LLM, CompletionResponse, ChatResponse, ChatMessage, LLMMetadata
import requests
from src.config.app_settings import AppSettings
from pydantic import Field
import logging
from src.config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class OllamaLLM(LLM):
    model: str = Field(default=AppSettings.QA_MODEL, description="Ollama QA model name")
    url: str = Field(default=f"{AppSettings.OLLAMA_BASE_URL}/api/generate", description="Ollama generate API endpoint")

    def __init__(self, model: str = None):
        super().__init__(model_name=model or AppSettings.QA_MODEL)

    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        try:
            response = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("response")
            if content is None:
                raise ValueError("Missing 'response' in Ollama server response")
            return CompletionResponse(text=content)
        except Exception as e:
            logger.exception(f"LLM completion failed.")
            raise RuntimeError(f"Failed to get completion: {str(e)}") from e

    def chat(self, messages: list[ChatMessage], **kwargs) -> ChatResponse:
        try:
            # Format messages for deepseek-r1:1.5b
            prompt = ""
            for m in messages:
                role = "user" if m.role == "user" else "assistant"
                prompt += f"[{role}] {m.content}\n"
            response = requests.post(
                self.url,
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=30
            )
            response.raise_for_status()
            content = response.json().get("response")
            if content is None:
                raise ValueError("Missing 'response' in Ollama server response")
            return ChatResponse(message=ChatMessage(role="assistant", content=content))
        except Exception as e:
            logger.exception(f"LLM chat failed.")
            raise RuntimeError(f"Failed to get chat response: {str(e)}") from e

    async def acomplete(self, prompt: str, **kwargs) -> CompletionResponse:
        raise NotImplementedError("Async complete not implemented")

    def stream_complete(self, prompt: str, **kwargs):
        raise NotImplementedError("Stream complete not implemented")

    async def astream_complete(self, prompt: str, **kwargs):
        raise NotImplementedError("Async stream complete not implemented")

    async def achat(self, messages: list[ChatMessage], **kwargs) -> ChatResponse:
        raise NotImplementedError("Async chat not implemented")

    def stream_chat(self, messages: list[ChatMessage], **kwargs):
        raise NotImplementedError("Stream chat not implemented")

    async def astream_chat(self, messages: list[ChatMessage], **kwargs):
        raise NotImplementedError("Async stream chat not implemented")

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=2048,
            num_output=512,
            is_chat_model=True,
            is_function_calling_model=False,
            model_name=self.model,
        )