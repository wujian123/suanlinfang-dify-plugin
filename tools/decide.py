from __future__ import annotations

import json
from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools._client import SuanlinfangApiError, request_json


class DecideTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        api_key = self.runtime.credentials.get("api_key")
        state_raw = (tool_parameters.get("state") or "").strip()
        if not state_raw:
            yield self.create_text_message("state 不能为空")
            return
        questions_raw = (tool_parameters.get("questions") or "").strip()
        if not questions_raw:
            yield self.create_text_message("questions 不能为空（JSON 字符串）")
            return
        # state 允许自由文本或 JSON；合法 JSON 则按结构传，否则按原文传
        state: Any
        try:
            state = json.loads(state_raw)
        except ValueError:
            state = state_raw
        try:
            questions = json.loads(questions_raw)
            if not isinstance(questions, dict):
                raise ValueError("questions 必须是 {题目id: 题目} JSON 映射")
        except ValueError as exc:
            yield self.create_text_message(f"questions 不是合法的 JSON 映射：{exc}")
            return
        try:
            body = request_json(
                "POST", "/systemone", api_key, json={"state": state, "questions": questions}
            )
        except SuanlinfangApiError as exc:
            yield self.create_text_message(str(exc))
            return
        yield self.create_json_message(
            {
                "inferenceId": body.get("inferenceId", ""),
                "answers": body.get("answers") or {},
                "usage": body.get("usage") or {},
            }
        )
