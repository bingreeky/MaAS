"""RAG LLM."""
import asyncio
from typing import Any

from llama_index.core.constants import DEFAULT_CONTEXT_WINDOW
from llama_index.core.llms import (
    CompletionResponse,
    CompletionResponseGen,
    CustomLLM,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_completion_callback
from pydantic import Field

from maas.config2 import config
from maas.llm import LLM
from maas.provider.base_llm import BaseLLM
from maas.utils.async_helper import NestAsyncio
from maas.utils.token_counter import TOKEN_MAX


class RAGLLM(CustomLLM):
    """LlamaIndex's LLM is different from MetaGPT's LLM.

    Inherit CustomLLM from llamaindex, making MetaGPT's LLM can be used by LlamaIndex.

    Set context_length or max_token of LLM in config.yaml if you encounter "Calculated available context size -xxx was not non-negative" error.
    """

    model_infer: BaseLLM = Field(..., description="The MetaGPT's LLM.")
    context_window: int = config.llm.context_length or TOKEN_MAX.get(config.llm.model, DEFAULT_CONTEXT_WINDOW)
    num_output: int = config.llm.max_token
    model_name: str = config.llm.model

    @property
    def metadata(self) -> LLMMetadata:
        """Get LLM metadata."""
        return LLMMetadata(
            context_window=self.context_window, num_output=self.num_output, model_name=self.model_name or "unknown"
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        NestAsyncio.apply_once()
        return asyncio.get_event_loop().run_until_complete(self.acomplete(prompt, **kwargs))

    @llm_completion_callback()
    async def acomplete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        text = await self.model_infer.aask(msg=prompt, stream=False)
        return CompletionResponse(text=text)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        ...


def get_rag_llm(model_infer: BaseLLM = None) -> RAGLLM:
    """Get llm that can be used by LlamaIndex."""
    return RAGLLM(model_infer=model_infer or LLM())
