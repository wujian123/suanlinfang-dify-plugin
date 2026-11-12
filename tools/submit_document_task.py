from __future__ import annotations

from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools._client import SuanlinfangApiError, submit_ocr_task_from_url

POLL_HINT = "建议每 10~30 秒用 get_document_task 查询一次"


class SubmitDocumentTaskTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = self.runtime.credentials.get("api_key")
        document_url = (tool_parameters.get("document_url") or "").strip()
        if not document_url:
            yield self.create_text_message("document_url 不能为空（公网 PDF URL）")
            return
        tier = (tool_parameters.get("tier") or "standard").strip() or "standard"
        prompt = (tool_parameters.get("prompt") or "").strip() or None
        file_name = (tool_parameters.get("file_name") or "").strip() or None
        try:
            task_no = submit_ocr_task_from_url(
                api_key, document_url, tier=tier, prompt=prompt, file_name=file_name
            )
        except SuanlinfangApiError as exc:
            yield self.create_text_message(str(exc))
            return
        yield self.create_json_message({"taskNo": task_no, "hint": POLL_HINT})
