from __future__ import annotations

from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools._client import SuanlinfangApiError, validate_api_key


class SuanlinfangProvider(ToolProvider):
    """凭据校验：GET /tts/voices 只读、不计费、无请求体，保存凭据时安全调用。"""

    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        api_key = credentials.get("api_key")
        if not api_key or not str(api_key).strip():
            raise ToolProviderCredentialValidationError(
                "算邻坊 API Key 缺失，请在插件凭据中填写"
            )
        try:
            validate_api_key(str(api_key).strip())
        except SuanlinfangApiError as exc:
            raise ToolProviderCredentialValidationError(str(exc)) from None
        except Exception as exc:
            raise ToolProviderCredentialValidationError(
                f"无法访问算邻坊 API 校验 Key：{exc}"
            ) from None
