from google.genai import types

from datalens.provider import Reply


def tool(name, **args):
    return types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(name=name, args=args))])


def final(answer="Analysis complete [E1].", status="completed", evidence_ids=None):
    return tool("final_answer", status=status, answer=answer, evidence_ids=["E1"] if evidence_ids is None else evidence_ids)


class ScriptedProvider:
    """Deterministic test double. This is NEVER proof of a live LLM call."""
    name = "scripted_test_double"

    def __init__(self, steps):
        self.steps = iter(steps)
        self.calls = 0

    async def count(self, *args):
        return 200

    async def generate(self, *args):
        self.calls += 1
        content = next(self.steps)
        if isinstance(content, Exception):
            raise content
        return Reply(content, 200, 80)
