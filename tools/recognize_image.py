from __future__ import annotations

from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools._client import SuanlinfangApiError, request_json


class RecognizeImageTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = self.runtime.credentials.get("api_key")
        image_url = (tool_parameters.get("image_url") or "").strip()
        if not image_url:
            yield self.create_text_message("image_url 不能为空（公网图片 URL）")
            return
        tier = (tool_parameters.get("tier") or "standard").strip() or "standard"
        form: dict[str, Any] = {"url": image_url, "tier": tier}
        prompt = (tool_parameters.get("prompt") or "").strip()
        if prompt:
            form["prompt"] = prompt
        try:
            body = request_json("POST", "/ocr/url", api_key, data=form)
        except SuanlinfangApiError as exc:
            yield self.create_text_message(str(exc))
            return
        words_result = body.get("wordsResult") or []
        yield self.create_json_message(
            {
                "logId": body.get("logId", ""),
                "words": [item.get("words", "") for item in words_result],
                "wordsResultNum": body.get("wordsResultNum", len(words_result)),
            }
        )
