from __future__ import annotations

from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools._client import SuanlinfangApiError, get_json_absolute, request_json


class GetTranscriptionTaskTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = self.runtime.credentials.get("api_key")
        task_no = (tool_parameters.get("task_no") or "").strip()
        if not task_no:
            yield self.create_text_message("task_no 不能为空")
            return
        try:
            body = request_json("GET", f"/stt/tasks/{task_no}", api_key)
            text = None
            if body.get("status") == "success" and body.get("resultUrl"):
                text = get_json_absolute(body["resultUrl"]).get("text")
        except SuanlinfangApiError as exc:
            yield self.create_text_message(str(exc))
            return
        payload: dict[str, Any] = {
            "status": body.get("status", ""),
            "totalUnits": body.get("totalUnits"),
            "doneUnits": body.get("doneUnits"),
        }
        if text is not None:
            payload["text"] = text
        if body.get("resultUrl"):
            payload["resultUrl"] = body["resultUrl"]
        if body.get("errorMsg"):
            payload["errorMsg"] = body["errorMsg"]
        yield self.create_json_message(payload)
