from __future__ import annotations

from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools._client import SuanlinfangApiError, request_json


class ListTtsVoicesTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = self.runtime.credentials.get("api_key")
        try:
            body = request_json("GET", "/tts/voices", api_key)
        except SuanlinfangApiError as exc:
            yield self.create_text_message(str(exc))
            return
        voices = body.get("voices")
        yield self.create_json_message({"voices": voices if isinstance(voices, list) else []})
