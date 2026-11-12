from __future__ import annotations

from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools._client import SuanlinfangApiError, request_json


class SynthesizeSpeechTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = self.runtime.credentials.get("api_key")
        text = tool_parameters.get("text") or ""
        if not text.strip():
            yield self.create_text_message("text 不能为空")
            return
        speaker = (tool_parameters.get("speaker") or "default").strip() or "default"
        audio_format = (tool_parameters.get("audio_format") or "wav").strip() or "wav"
        payload = {
            "reqParams": {"text": text, "speaker": speaker},
            "audioParams": {"format": audio_format},
        }
        try:
            body = request_json("POST", "/tts", api_key, json=payload)
        except SuanlinfangApiError as exc:
            yield self.create_text_message(str(exc))
            return
        yield self.create_json_message(
            {
                "url": body.get("url", ""),
                "durationMs": body.get("durationMs"),
                "inferenceId": body.get("inferenceId", ""),
            }
        )
