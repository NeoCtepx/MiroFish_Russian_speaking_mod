"""OpenAI-compatible LLM client with robust JSON parsing.

This file is intentionally ASCII-only.
"""

import json
import os
import re
from typing import Optional, Dict, Any, List

from openai import OpenAI

from ..config import Config


class LLMClient:
    """Small OpenAI-compatible LLM wrapper."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("LLM_API_KEY is not configured")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _is_nvidia(self) -> bool:
        value = (self.base_url or "").lower()
        return "nvidia.com" in value or "integrate.api.nvidia.com" in value

    def _strip_reasoning(self, content: str) -> str:
        if content is None:
            return ""
        text = str(content)
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.IGNORECASE | re.DOTALL)
        return text.strip()

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
    ) -> str:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        use_response_format = response_format is not None and not self._is_nvidia()
        if use_response_format:
            kwargs["response_format"] = response_format

        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception:
            if "response_format" in kwargs:
                kwargs.pop("response_format", None)
                response = self.client.chat.completions.create(**kwargs)
            else:
                raise

        content = response.choices[0].message.content
        return self._strip_reasoning(content)

    def _json_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        result = list(messages)
        instruction = (
            "Return only one valid JSON object. "
            "Do not use markdown. "
            "Do not wrap the JSON in code fences. "
            "Do not add comments or explanations."
        )
        if result and result[0].get("role") == "system":
            result[0] = {
                "role": "system",
                "content": str(result[0].get("content", "")) + "\n\n" + instruction,
            }
        else:
            result.insert(0, {"role": "system", "content": instruction})
        return result

    def _parse_json_object(self, text: str) -> Dict[str, Any]:
        raw = "" if text is None else str(text).strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

        decoder = json.JSONDecoder()
        for idx, char in enumerate(raw):
            if char not in "{[":
                continue
            try:
                obj, _end = decoder.raw_decode(raw[idx:])
            except Exception:
                continue
            if isinstance(obj, dict):
                return obj

        preview = raw[:1200].replace("\n", "\\n")
        raise ValueError("LLM returned invalid JSON object: " + preview)

    def _repair_json(self, bad_text: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You repair malformed model output into one valid JSON object. "
                    "Return JSON only. No markdown."
                ),
            },
            {
                "role": "user",
                "content": "Repair this into one valid JSON object:\n\n" + str(bad_text),
            },
        ]
        fixed = self.chat(messages=messages, temperature=temperature, max_tokens=max_tokens)
        return self._parse_json_object(fixed)

    def _looks_like_ontology_request(self, messages: List[Dict[str, str]]) -> bool:
        joined = "\n".join(str(m.get("content", "")) for m in messages).lower()
        markers = ["entity_types", "edge_types", "analysis_summary", "ontology"]
        return sum(1 for marker in markers if marker in joined) >= 2

    def _fallback_ontology(self) -> Dict[str, Any]:
        return {
            "entity_types": [
                {
                    "name": "PublicFigure",
                    "description": "A visible person who can influence public discussion.",
                    "attributes": [
                        {"name": "full_name", "type": "text", "description": "Full name"},
                        {"name": "role", "type": "text", "description": "Public role"},
                    ],
                    "examples": ["public speaker", "known author"],
                },
                {
                    "name": "Official",
                    "description": "A public official or policy decision maker.",
                    "attributes": [
                        {"name": "full_name", "type": "text", "description": "Full name"},
                        {"name": "position", "type": "text", "description": "Official position"},
                    ],
                    "examples": ["minister", "regulator"],
                },
                {
                    "name": "Expert",
                    "description": "A specialist who comments on the topic.",
                    "attributes": [
                        {"name": "full_name", "type": "text", "description": "Full name"},
                        {"name": "expertise", "type": "text", "description": "Area of expertise"},
                    ],
                    "examples": ["analyst", "researcher"],
                },
                {
                    "name": "Customer",
                    "description": "A person affected as a buyer or user.",
                    "attributes": [
                        {"name": "segment", "type": "text", "description": "Customer segment"},
                        {"name": "concern", "type": "text", "description": "Main concern"},
                    ],
                    "examples": ["new user", "returning buyer"],
                },
                {
                    "name": "CommunityGroup",
                    "description": "A group of people sharing an interest or concern.",
                    "attributes": [
                        {"name": "group_name", "type": "text", "description": "Group name"},
                        {"name": "interest", "type": "text", "description": "Shared interest"},
                    ],
                    "examples": ["fan group", "local community"],
                },
                {
                    "name": "Company",
                    "description": "A business organization involved in the situation.",
                    "attributes": [
                        {"name": "org_name", "type": "text", "description": "Company name"},
                        {"name": "industry", "type": "text", "description": "Industry"},
                    ],
                    "examples": ["vendor", "platform company"],
                },
                {
                    "name": "MediaOutlet",
                    "description": "A media source that publishes or amplifies information.",
                    "attributes": [
                        {"name": "org_name", "type": "text", "description": "Outlet name"},
                        {"name": "channel", "type": "text", "description": "Media channel"},
                    ],
                    "examples": ["news site", "blog"],
                },
                {
                    "name": "Platform",
                    "description": "A digital platform where interaction happens.",
                    "attributes": [
                        {"name": "platform_name", "type": "text", "description": "Platform name"},
                        {"name": "platform_type", "type": "text", "description": "Platform type"},
                    ],
                    "examples": ["social network", "marketplace"],
                },
                {
                    "name": "Person",
                    "description": "Any individual person not fitting other specific person types.",
                    "attributes": [
                        {"name": "full_name", "type": "text", "description": "Full name"},
                        {"name": "role", "type": "text", "description": "Role or occupation"},
                    ],
                    "examples": ["ordinary citizen", "anonymous user"],
                },
                {
                    "name": "Organization",
                    "description": "Any organization not fitting other specific organization types.",
                    "attributes": [
                        {"name": "org_name", "type": "text", "description": "Organization name"},
                        {"name": "org_type", "type": "text", "description": "Organization type"},
                    ],
                    "examples": ["small business", "association"],
                },
            ],
            "edge_types": [
                {
                    "name": "COMMENTS_ON",
                    "description": "One entity publicly comments on another entity or event.",
                    "source_targets": [{"source": "Person", "target": "Organization"}],
                    "attributes": [],
                },
                {
                    "name": "INFLUENCES",
                    "description": "One entity affects opinions or actions of another.",
                    "source_targets": [{"source": "PublicFigure", "target": "CommunityGroup"}],
                    "attributes": [],
                },
                {
                    "name": "REPORTS_ON",
                    "description": "A media outlet reports on an entity.",
                    "source_targets": [{"source": "MediaOutlet", "target": "Organization"}],
                    "attributes": [],
                },
                {
                    "name": "WORKS_FOR",
                    "description": "A person works for an organization.",
                    "source_targets": [{"source": "Person", "target": "Organization"}],
                    "attributes": [],
                },
                {
                    "name": "REPRESENTS",
                    "description": "An entity represents another entity or group.",
                    "source_targets": [{"source": "Official", "target": "Organization"}],
                    "attributes": [],
                },
                {
                    "name": "USES_PLATFORM",
                    "description": "An entity communicates or acts through a platform.",
                    "source_targets": [{"source": "Person", "target": "Platform"}],
                    "attributes": [],
                },
            ],
            "analysis_summary": (
                "Generic ontology fallback was used because the configured LLM did not return "
                "a parseable JSON object. Check backend logs and LLM credentials for quality."
            ),
        }

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        json_messages = self._json_messages(messages)
        errors = []
        last_text = ""

        for label, response_format in (
            ("plain-json-prompt", None),
            ("openai-json-object", {"type": "json_object"}),
        ):
            try:
                if response_format is not None and self._is_nvidia():
                    continue
                last_text = self.chat(
                    messages=json_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
                return self._parse_json_object(last_text)
            except Exception as exc:
                errors.append(label + ": " + repr(exc))

        if last_text:
            try:
                return self._repair_json(last_text, temperature=0.1, max_tokens=max_tokens)
            except Exception as exc:
                errors.append("repair: " + repr(exc))

        allow_fallback = os.getenv("MIROFISH_ONTOLOGY_FALLBACK", "1").strip().lower()
        if allow_fallback not in ("0", "false", "no") and self._looks_like_ontology_request(messages):
            print("[mirofish] ontology fallback used after LLM JSON failure: " + " | ".join(errors), flush=True)
            return self._fallback_ontology()

        raise ValueError("LLM JSON generation failed: " + " | ".join(errors))
