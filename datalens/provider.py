import math
from dataclasses import dataclass

from google import genai
from google.genai import types

from datalens.config import Settings


class ConfigurationError(Exception):
    pass


@dataclass
class Reply:
    content: types.Content
    input_tokens: int | None
    output_tokens: int | None


class Gemini:
    name = "gemini"

    def __init__(self, settings: Settings, api_key: str):
        if not api_key.strip():
            raise ConfigurationError("GEMINI_API_KEY is missing. Add it to deployment secrets or enter your key.")
        self.settings = settings
        self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(
            timeout=settings.timeout_seconds * 1000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ))

    async def count(self, contents, system, tools):
        # Pre-call budget guard: use a deliberately conservative local estimate.
        # This avoids making a separate count_tokens API request, whose accepted
        # config surface can differ from generate_content across Gemini releases.
        # Exact cost is settled after each generation from provider usage metadata.
        chars = len(system)
        chars += sum(len(item.model_dump_json(exclude_none=True)) for item in contents)
        chars += sum(len(tool.model_dump_json(exclude_none=True)) for tool in tools)
        return math.ceil(chars / 2) + 512

    async def generate(self, contents, system, tools):
        # Preserve returned Content unchanged, including any opaque thought signatures.
        thinking = (types.ThinkingConfig(thinking_budget=0) if "2.5" in self.settings.model
                    else types.ThinkingConfig(thinking_level="MINIMAL"))
        response = await self.client.aio.models.generate_content(
            model=self.settings.model, contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system, tools=tools, temperature=0,
                max_output_tokens=self.settings.max_output_tokens,
                thinking_config=thinking,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        usage = response.usage_metadata
        inp = usage.prompt_token_count if usage else None
        out = None
        if usage and usage.candidates_token_count is not None:
            out = usage.candidates_token_count + (usage.thoughts_token_count or 0)
        content = (response.candidates[0].content if response.candidates else None)
        return Reply(content or types.Content(role="model", parts=[]), inp, out)

    async def close(self):
        await self.client.aio.aclose()
        self.client.close()
