from __future__ import annotations

import json
import os
import time
from typing import Any

from .telemetry import estimate_tokens


class OpenAIResponsesJSONClient:
    """Strict-schema JSON client for reproducible OpenAI Responses API experiments.

    The response schema is fixed when the client is constructed. This keeps the
    SH2026 experimental condition explicit while remaining compatible with the
    small ``complete_json`` protocol used by the evidence-first extractors.
    """

    provider = "openai"

    def __init__(
        self,
        *,
        model: str,
        response_schema: dict[str, Any],
        schema_name: str,
        reasoning_effort: str = "none",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        if not model:
            raise ValueError("An explicit OpenAI model identifier is required")
        if not schema_name:
            raise ValueError("schema_name is required")
        self.model = model
        self.response_schema = response_schema
        self.schema_name = schema_name
        self.reasoning_effort = reasoning_effort
        self.api_key = api_key
        self.base_url = base_url

    def complete_json(self, task: str, prompt: str, *, input_text: str | None = None) -> dict[str, Any]:
        start = time.perf_counter()
        raw_text = ""
        response_id = None
        resolved_model = self.model
        input_tokens = None
        output_tokens = None
        error = None
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key or os.getenv("OPENAI_API_KEY"),
                base_url=self.base_url,
            )
            if not hasattr(client, "responses"):
                raise RuntimeError(
                    "Installed openai package does not expose the Responses API; upgrade the optional llm dependency."
                )
            response = client.responses.create(
                model=self.model,
                input=prompt,
                reasoning={"effort": self.reasoning_effort},
                text={
                    "format": {
                        "type": "json_schema",
                        "name": self.schema_name,
                        "schema": self.response_schema,
                        "strict": True,
                    }
                },
                store=False,
            )
            raw_text = response.output_text or "{}"
            data = json.loads(raw_text)
            if not isinstance(data, dict):
                raise ValueError("Structured response must decode to a JSON object")
            response_id = getattr(response, "id", None)
            resolved_model = getattr(response, "model", None) or self.model
            usage = getattr(response, "usage", None)
            input_tokens = getattr(usage, "input_tokens", None) if usage is not None else None
            output_tokens = getattr(usage, "output_tokens", None) if usage is not None else None
        except Exception as exc:
            error = str(exc)
            data = {}

        latency_ms = round((time.perf_counter() - start) * 1000, 3)
        data["telemetry"] = {
            "task": task,
            "backend": "llm",
            "provider": self.provider,
            "model": resolved_model,
            "api": "responses",
            "reasoning_effort": self.reasoning_effort,
            "latency_ms": latency_ms,
            "input_chars": len(input_text if input_text is not None else prompt),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_tokens_est": input_tokens if input_tokens is not None else estimate_tokens(prompt),
            "output_tokens_est": output_tokens if output_tokens is not None else estimate_tokens(raw_text),
            "cost_usd_est": None,
            "success": error is None,
            "error": error,
        }
        data["_raw_response_text"] = raw_text
        data["_response_metadata"] = {
            "response_id": response_id,
            "requested_model": self.model,
            "resolved_model": resolved_model,
            "api": "responses",
            "schema_name": self.schema_name,
            "reasoning_effort": self.reasoning_effort,
            "store": False,
        }
        return data
