"""
Unified LLM client with automatic provider detection and fallback.

Priority order:
  1. Anthropic  (claude-sonnet-4-6)           — ANTHROPIC_API_KEY
  2. Google     (gemini-2.0-flash)            — Vertex AI ADC (no key on Cloud Run)
  3. Google     (gemini-2.0-flash)            — GOOGLE_API_KEY (local dev)
  4. Groq       (llama-3.3-70b-versatile)     — GROQ_API_KEY (free tier)
  5. Ollama     (best locally available)      — no key needed

All providers return a NormalizedResponse so agents need zero changes across providers.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from typing import Optional

import requests as _requests


# ── Normalised response types (mimic Anthropic SDK shape) ─────────────────────

@dataclass
class NormalizedTextBlock:
    text: str
    type: str = "text"


@dataclass
class NormalizedToolUseBlock:
    id: str
    name: str
    input: dict
    type: str = "tool_use"


@dataclass
class NormalizedResponse:
    content: list
    stop_reason: str  # "end_turn" | "tool_use"


# ── Provider detection ────────────────────────────────────────────────────────

_PREFERRED_OLLAMA_MODELS = [
    "qwen2.5:14b", "qwen2.5:7b",
    "llama3.1:70b", "llama3.1:8b",
    "llama3.2:latest", "mistral:latest",
]


def _pick_ollama_model(available: list[str]) -> Optional[str]:
    available_lower = {m.lower() for m in available}
    for preferred in _PREFERRED_OLLAMA_MODELS:
        if preferred.lower() in available_lower:
            return preferred
    return available[0] if available else None


def _detect_provider() -> tuple[str, object, str]:
    # ── 1. Anthropic ──────────────────────────────────────────────────────────
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key and not key.startswith("your_") and len(key) > 20:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            print("[LLM] Using Anthropic claude-sonnet-4-6")
            return ("anthropic", client, "claude-sonnet-4-6")
        except Exception as exc:
            print(f"[LLM] Anthropic init failed: {exc}")

    # ── 2. Google Gemini via native SDK + Vertex AI ADC (Cloud Run) ───────────
    try:
        from google import genai as _genai
        _genai_client = _genai.Client(vertexai=True)
        _genai_client.models.generate_content(model="gemini-2.0-flash", contents="hi")
        print("[LLM] Using Gemini 2.0 Flash (google-genai SDK, Vertex AI ADC)")
        return ("gemini_native", _genai_client, "gemini-2.0-flash")
    except Exception as exc:
        print(f"[LLM] Gemini native ADC not available: {exc}")

    # ── 3. Google Gemini via API key (local dev) ───────────────────────────────
    key = os.environ.get("GOOGLE_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
    if key and not key.startswith("your_"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            print("[LLM] Using Gemini 2.0 Flash (API key)")
            return ("gemini", client, "gemini-2.0-flash")
        except Exception as exc:
            print(f"[LLM] Gemini API key init failed: {exc}")

    # ── 4. Groq (free tier) ────────────────────────────────────────────────────
    key = os.environ.get("GROQ_API_KEY", "")
    if key and not key.startswith("your_"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            for model in ["llama3-groq-70b-8192-tool-use-preview", "llama-3.3-70b-versatile"]:
                try:
                    client.chat.completions.create(model=model, messages=[{"role": "user", "content": "hi"}], max_tokens=1)
                    print(f"[LLM] Using Groq {model}")
                    return ("groq", client, model)
                except Exception:
                    continue
        except Exception as exc:
            print(f"[LLM] Groq init failed: {exc}")

    # ── 5. Ollama (local) ──────────────────────────────────────────────────────
    try:
        resp = _requests.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            chosen = _pick_ollama_model(models)
            if chosen:
                from openai import OpenAI
                client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
                print(f"[LLM] Using Ollama {chosen}")
                return ("ollama", client, chosen)
    except Exception:
        pass

    raise RuntimeError(
        "No LLM provider available.\n"
        "Options:\n"
        "  1. Set ANTHROPIC_API_KEY in .env\n"
        "  2. Set GOOGLE_API_KEY in .env  (aistudio.google.com, free)\n"
        "  3. Set GROQ_API_KEY in .env    (console.groq.com, free)\n"
        "  4. Install Ollama: https://ollama.com, then: ollama pull llama3.2"
    )


# ── Format converters ─────────────────────────────────────────────────────────

def _anthropic_tools_to_openai(tools: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
            },
        }
        for t in (tools or [])
    ]


def _anthropic_messages_to_openai(messages: list[dict]) -> list[dict]:
    out = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            if isinstance(content, str):
                out.append({"role": "user", "content": content})
            elif isinstance(content, list):
                tool_results = [c for c in content if isinstance(c, dict) and c.get("type") == "tool_result"]
                if tool_results:
                    for tr in tool_results:
                        body = tr.get("content", "")
                        out.append({
                            "role": "tool",
                            "tool_call_id": tr.get("tool_use_id", ""),
                            "content": body if isinstance(body, str) else json.dumps(body),
                        })
                else:
                    text = " ".join(
                        (b.get("text", "") if isinstance(b, dict) else getattr(b, "text", ""))
                        for b in content
                    )
                    out.append({"role": "user", "content": text or str(content)})

        elif role == "assistant":
            if isinstance(content, str):
                out.append({"role": "assistant", "content": content})
            elif isinstance(content, list):
                text_parts: list[str] = []
                tool_calls: list[dict] = []
                for block in content:
                    btype = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
                    if btype == "text":
                        txt = block.get("text") if isinstance(block, dict) else getattr(block, "text", "")
                        if txt:
                            text_parts.append(txt)
                    elif btype == "tool_use":
                        bid = block.get("id") if isinstance(block, dict) else getattr(block, "id", "")
                        bname = block.get("name") if isinstance(block, dict) else getattr(block, "name", "")
                        binput = block.get("input", {}) if isinstance(block, dict) else getattr(block, "input", {})
                        tool_calls.append({
                            "id": bid,
                            "type": "function",
                            "function": {"name": bname, "arguments": json.dumps(binput)},
                        })
                entry: dict = {"role": "assistant", "content": " ".join(text_parts) or None}
                if tool_calls:
                    entry["tool_calls"] = tool_calls
                out.append(entry)
    return out


def _openai_response_to_normalized(response) -> NormalizedResponse:
    choice = response.choices[0]
    msg = choice.message
    blocks: list = []
    stop_reason = "end_turn"

    if msg.content:
        blocks.append(NormalizedTextBlock(text=msg.content))

    if hasattr(msg, "tool_calls") and msg.tool_calls:
        stop_reason = "tool_use"
        for tc in msg.tool_calls:
            try:
                input_dict = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                input_dict = {"_raw": tc.function.arguments}
            blocks.append(NormalizedToolUseBlock(id=tc.id, name=tc.function.name, input=input_dict))

    if choice.finish_reason == "tool_calls":
        stop_reason = "tool_use"

    return NormalizedResponse(content=blocks, stop_reason=stop_reason)


def _anthropic_to_genai_tools(tools: list[dict]) -> list:
    from google.genai import types as _gt
    declarations = []
    for t in (tools or []):
        schema = t.get("input_schema", {"type": "object", "properties": {}})
        declarations.append(_gt.FunctionDeclaration(
            name=t["name"],
            description=t.get("description", ""),
            parameters=schema,
        ))
    return [_gt.Tool(function_declarations=declarations)]


def _anthropic_messages_to_genai(messages: list[dict]) -> list:
    from google.genai import types as _gt

    tool_id_to_name: dict[str, str] = {}
    for msg in messages:
        content = msg.get("content", [])
        if isinstance(content, list):
            for block in content:
                btype = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
                if btype == "tool_use":
                    bid = block.get("id") if isinstance(block, dict) else getattr(block, "id", "")
                    bname = block.get("name") if isinstance(block, dict) else getattr(block, "name", "")
                    tool_id_to_name[bid] = bname

    contents = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        genai_role = "model" if role == "assistant" else "user"

        if isinstance(content, str):
            contents.append(_gt.Content(role=genai_role, parts=[_gt.Part(text=content)]))
            continue

        if not isinstance(content, list):
            continue

        tool_results = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_result"]
        if tool_results:
            parts = []
            for tr in tool_results:
                tool_use_id = tr.get("tool_use_id", "")
                tool_name = tool_id_to_name.get(tool_use_id, tool_use_id)
                result_body = tr.get("content", "")
                if isinstance(result_body, list):
                    result_body = json.dumps(result_body)
                parts.append(_gt.Part(
                    function_response=_gt.FunctionResponse(name=tool_name, response={"result": result_body})
                ))
            if parts:
                contents.append(_gt.Content(role="user", parts=parts))
            continue

        parts = []
        for block in content:
            btype = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
            if btype == "text":
                txt = block.get("text") if isinstance(block, dict) else getattr(block, "text", "")
                if txt:
                    parts.append(_gt.Part(text=txt))
            elif btype == "tool_use":
                bname = block.get("name") if isinstance(block, dict) else getattr(block, "name", "")
                binput = block.get("input", {}) if isinstance(block, dict) else getattr(block, "input", {})
                parts.append(_gt.Part(function_call=_gt.FunctionCall(name=bname, args=binput)))
        if parts:
            contents.append(_gt.Content(role=genai_role, parts=parts))

    return contents


def _genai_response_to_normalized(response) -> NormalizedResponse:
    blocks: list = []
    stop_reason = "end_turn"

    if not response.candidates:
        return NormalizedResponse(content=blocks, stop_reason=stop_reason)

    candidate = response.candidates[0]
    if not candidate.content or not candidate.content.parts:
        return NormalizedResponse(content=blocks, stop_reason=stop_reason)

    for part in candidate.content.parts:
        if hasattr(part, "text") and part.text:
            blocks.append(NormalizedTextBlock(text=part.text))
        if hasattr(part, "function_call") and part.function_call:
            fc = part.function_call
            stop_reason = "tool_use"
            blocks.append(NormalizedToolUseBlock(
                id=f"toolu_{uuid.uuid4().hex[:24]}",
                name=fc.name,
                input=dict(fc.args) if fc.args else {},
            ))

    return NormalizedResponse(content=blocks, stop_reason=stop_reason)


def _anthropic_response_to_normalized(response) -> NormalizedResponse:
    blocks = []
    for block in response.content:
        if block.type == "text":
            blocks.append(NormalizedTextBlock(text=block.text))
        elif block.type == "tool_use":
            blocks.append(NormalizedToolUseBlock(id=block.id, name=block.name, input=block.input))
    return NormalizedResponse(content=blocks, stop_reason=response.stop_reason or "end_turn")


# ── Public client ─────────────────────────────────────────────────────────────

class UnifiedLLMClient:
    """
    Drop-in for anthropic.Anthropic(). Auto-detects best available provider.
    Call .messages_create() identically regardless of which provider is active.
    """

    def __init__(self):
        self.provider, self._client, self.model = _detect_provider()

    def messages_create(
        self,
        *,
        system: str,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        max_tokens: int = 4096,
        force_tool: Optional[str] = None,
    ) -> NormalizedResponse:
        if self.provider == "anthropic":
            return self._call_anthropic(system, messages, tools, max_tokens, force_tool)
        elif self.provider == "gemini_native":
            return self._call_genai(system, messages, tools, max_tokens, force_tool)
        else:
            return self._call_openai_compat(system, messages, tools, max_tokens, force_tool)

    def _call_anthropic(self, system, messages, tools, max_tokens, force_tool=None) -> NormalizedResponse:
        kwargs: dict = dict(model=self.model, max_tokens=max_tokens, system=system, messages=messages)
        if tools:
            kwargs["tools"] = tools
        if force_tool and tools:
            kwargs["tool_choice"] = {"type": "tool", "name": force_tool}
        raw = self._client.messages.create(**kwargs)
        return _anthropic_response_to_normalized(raw)

    def _call_genai(self, system, messages, tools, max_tokens, force_tool=None) -> NormalizedResponse:
        from google.genai import types as _gt
        contents = _anthropic_messages_to_genai(messages)
        config_kwargs: dict = dict(system_instruction=system, max_output_tokens=max_tokens)
        if tools:
            config_kwargs["tools"] = _anthropic_to_genai_tools(tools)
            config_kwargs["automatic_function_calling"] = _gt.AutomaticFunctionCallingConfig(disable=True)
            if force_tool:
                config_kwargs["tool_config"] = _gt.ToolConfig(
                    function_calling_config=_gt.FunctionCallingConfig(mode="ANY", allowed_function_names=[force_tool])
                )
        raw = self._client.models.generate_content(
            model=self.model,
            contents=contents,
            config=_gt.GenerateContentConfig(**config_kwargs),
        )
        return _genai_response_to_normalized(raw)

    def _call_openai_compat(self, system, messages, tools, max_tokens, force_tool=None) -> NormalizedResponse:
        openai_msgs = [{"role": "system", "content": system}] + _anthropic_messages_to_openai(messages)
        kwargs: dict = dict(model=self.model, max_tokens=max_tokens, messages=openai_msgs)
        if tools:
            kwargs["tools"] = _anthropic_tools_to_openai(tools)
            kwargs["tool_choice"] = (
                {"type": "function", "function": {"name": force_tool}} if force_tool else "auto"
            )
        raw = self._client.chat.completions.create(**kwargs)
        return _openai_response_to_normalized(raw)


_instance: Optional[UnifiedLLMClient] = None


def get_llm_client() -> UnifiedLLMClient:
    global _instance
    if _instance is None:
        _instance = UnifiedLLMClient()
    return _instance


def reset_llm_client():
    global _instance
    _instance = None
