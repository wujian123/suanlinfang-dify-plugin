from __future__ import annotations

from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools._client import SuanlinfangApiError, request_json


class TranscribeAudioTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = self.runtime.credentials.get("api_key")
        audio_url = (tool_parameters.get("audio_url") or "").strip()
        if not audio_url:
            yield self.create_text_message("audio_url 不能为空（公网音频 URL）")
            return
        form: dict[str, Any] = {"url": audio_url}
        language = (tool_parameters.get("language") or "").strip()
        if language:
            form["language"] = language
        context = (tool_parameters.get("context") or "").strip()
        if context:
            form["context"] = context
        try:
            body = request_json("POST", "/stt/url", api_key, data=form)
        except SuanlinfangApiError as exc:
            yield self.create_text_message(str(exc))
            return
        result = body.get("result") or {}
        audio_info = body.get("audioInfo") or {}
        yield self.create_json_message(
            {
                "text": result.get("text", ""),
                "durationMs": audio_info.get("durationMs"),
                "inferenceId": body.get("inferenceId", ""),
            }
        )
