from __future__ import annotations

from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools._client import SuanlinfangApiError, submit_stt_task_from_url

POLL_HINT = "建议每 10~30 秒用 get_transcription_task 查询一次（长音频按音频时长的 1/6~1/4 估算总耗时）"


class SubmitTranscriptionTaskTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = self.runtime.credentials.get("api_key")
        audio_url = (tool_parameters.get("audio_url") or "").strip()
        if not audio_url:
            yield self.create_text_message("audio_url 不能为空（公网音频 URL）")
            return
        language = (tool_parameters.get("language") or "").strip() or None
        context = (tool_parameters.get("context") or "").strip() or None
        file_name = (tool_parameters.get("file_name") or "").strip() or None
        try:
            task_no = submit_stt_task_from_url(
                api_key,
                audio_url,
                language=language,
                context=context,
                file_name=file_name,
            )
        except SuanlinfangApiError as exc:
            yield self.create_text_message(str(exc))
            return
        yield self.create_json_message({"taskNo": task_no, "hint": POLL_HINT})
