"""Shared HTTP client for all SuanLinFang tools.

直接对接算邻坊 REST 契约（https://suanlinfang.cn/v1），与官方 suanlinfang-sdk
同源的请求/错误处理约定：

- 鉴权：Authorization: Bearer <api_key>，key 来自插件凭据（secret-input），
  绝不写入日志、错误信息或返回值。
- 错误信封：非 2xx 响应为 {"error": {code, type, message}, "requestId"}，
  解析后抛 SuanlinfangApiError。
- 重试：502/503/504 按 Retry-After 或指数退避重试（最多 3 次）；超时不自动
  重试（计费可能已完成），抛可重试语义错误由调用方决策。
- 大文件链路（长音频/PDF 的 URL→任务）：流式下载到临时文件 → 申请上传凭证
  → OSS 直传 → 提交任务；OSS 与结果下载 URL 为运行时签发的绝对地址
  （*.aliyuncs.com），不带鉴权头，按凭证 headers 原样发送。
"""

from __future__ import annotations

import os
import tempfile
import time
from typing import Any, BinaryIO, Optional
from urllib.parse import urlparse

import requests

API_BASE_URL = "https://suanlinfang.cn/v1"
API_KEY_HELP_URL = "https://suanlinfang.cn/consume-web/api-keys.html"
DEFAULT_REQUEST_TIMEOUT = 60.0
MAX_RETRIES = 3
RETRY_STATUS = (502, 503, 504)

STT_MAX_TASK_BYTES = 500 * 1024 * 1024
STT_SUPPORTED_EXTENSIONS = (".wav", ".mp3", ".flac", ".m4a", ".ogg", ".aac")
OCR_PDF_MAX_BYTES = 200 * 1024 * 1024


class SuanlinfangApiError(Exception):
    """算邻坊 REST 非 2xx 响应或网络层失败。"""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_type: Optional[str] = None,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.error_type = error_type
        self.code = code
        self.request_id = request_id
        self.retryable = retryable

    def __str__(self) -> str:
        parts = [f"SuanLinFang API error {self.status_code}: {self.message}"]
        if self.status_code == 401:
            parts.append(
                f"API Key 无效或缺失，请在 {API_KEY_HELP_URL} 创建后填入插件凭据"
            )
        elif self.status_code == 402:
            parts.append("账户余额不足，请前往 suanlinfang.cn 充值后重试")
        if self.request_id:
            parts.append(f"requestId: {self.request_id}")
        if self.retryable:
            parts.append("该错误可直接重试")
        return "；".join(parts)


def _auth_headers(api_key: str) -> dict[str, str]:
    # Content-Type 不在此设置：json=/data= 由 requests 按请求体类型自动带
    return {"Authorization": f"Bearer {api_key}"}


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def _retry_after_seconds(response: requests.Response) -> float | None:
    raw = response.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _raise_for_error(response: requests.Response) -> None:
    if response.ok:
        return
    message = response.text[:500]
    error_type = None
    code = None
    request_id = response.headers.get("X-Request-Id")
    try:
        body = response.json()
        error = body.get("error") or {}
        message = error.get("message") or message
        error_type = error.get("type")
        code = error.get("code")
        request_id = body.get("requestId") or request_id
    except ValueError:
        pass
    raise SuanlinfangApiError(
        response.status_code,
        message,
        error_type=error_type,
        code=code,
        request_id=request_id,
        retryable=response.status_code >= 500,
    )


def request_json(
    method: str,
    path: str,
    api_key: str,
    *,
    json: Any | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """带鉴权的 JSON 请求（相对路径拼接 base_url），含 5xx 退避重试。"""
    url = path if path.startswith("http") else f"{API_BASE_URL}{path}"
    retries = 0
    while True:
        response = requests.request(
            method,
            url,
            json=json,
            data=data,
            headers=_auth_headers(api_key),
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )
        if response.status_code in RETRY_STATUS and retries < MAX_RETRIES:
            retries += 1
            delay = _retry_after_seconds(response) or 0.5 * (2 ** (retries - 1))
            _sleep(delay)
            continue
        break
    _raise_for_error(response)
    try:
        body = response.json()
    except ValueError:
        raise SuanlinfangApiError(
            response.status_code, "响应不是合法 JSON", retryable=False
        ) from None
    return body if isinstance(body, dict) else {"_list": body}


def get_json_absolute(url: str) -> dict[str, Any]:
    """下载并解析运行时签发的结果 URL（result.json 等）：无鉴权。"""
    response = requests.get(url, timeout=DEFAULT_REQUEST_TIMEOUT)
    _raise_for_error(response)
    body = response.json()
    return body if isinstance(body, dict) else {"_list": body}


def put_bytes(url: str, content: bytes | BinaryIO, headers: dict[str, str]) -> None:
    """OSS 直传：成功 200 无响应体，非 2xx 直接抛。"""
    response = requests.put(url, data=content, headers=headers, timeout=300)
    _raise_for_error(response)


def stream_to_file(url: str, file_path: str, max_bytes: int) -> int:
    """流式下载到本地文件（长音频/PDF 的 URL→任务链路），返回实际字节数；超上限抛错。"""
    written = 0
    with requests.get(url, stream=True, timeout=DEFAULT_REQUEST_TIMEOUT) as response:
        _raise_for_error(response)
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > max_bytes:
            raise SuanlinfangApiError(
                413,
                f"远端文件 {int(content_length)} 字节，超过上限 {max_bytes} 字节",
                error_type="request_too_large",
                retryable=False,
            )
        with open(file_path, "wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                written += len(chunk)
                if written > max_bytes:
                    raise SuanlinfangApiError(
                        413,
                        f"下载超过上限 {max_bytes} 字节，中止",
                        error_type="request_too_large",
                        retryable=False,
                    )
                output.write(chunk)
    return written


def validate_api_key(api_key: str) -> None:
    """凭据校验：GET /tts/voices 只读、不计费、无请求体。"""
    request_json("GET", "/tts/voices", api_key)


def request_upload_ticket(api_key: str, product: str, file_name: str, size_bytes: int) -> dict[str, Any]:
    """申请上传凭证（product: stt/ocr），返回 {fileKey, uploadUrl, method, headers, ...}。"""
    return request_json(
        "POST",
        f"/{product}/upload-tickets",
        api_key,
        json={"fileName": file_name, "sizeBytes": size_bytes},
    )


def _derive_file_name(url: str, file_name: str | None, fallback: str) -> str:
    return file_name or os.path.basename(urlparse(url).path) or fallback


def submit_stt_task_from_url(
    api_key: str,
    url: str,
    *,
    language: str | None = None,
    context: str | None = None,
    file_name: str | None = None,
) -> str:
    """长音频 URL→任务：流式下载（≤500MB）→ 签名 → OSS 直传 → 提交，返回 taskNo。"""
    derived_name = _derive_file_name(url, file_name, "audio.mp3")
    extension = os.path.splitext(derived_name)[1].lower()
    if extension not in STT_SUPPORTED_EXTENSIONS:
        raise SuanlinfangApiError(
            400,
            f"音频扩展名 {extension or '(无)'} 不受支持"
            f"（{'/'.join(STT_SUPPORTED_EXTENSIONS)}）；请通过 file_name 指定正确扩展名",
            retryable=False,
        )
    with tempfile.TemporaryDirectory(prefix="suanlinfang-stt-") as tmp_dir:
        local_path = os.path.join(tmp_dir, derived_name)
        size_bytes = stream_to_file(url, local_path, STT_MAX_TASK_BYTES)
        with open(local_path, "rb") as audio_file:
            ticket = request_upload_ticket(api_key, "stt", derived_name, size_bytes)
            # 流式上传（文件对象直传，500MB 级不整读进内存）
            put_bytes(ticket["uploadUrl"], audio_file, ticket.get("headers") or {})
    payload: dict[str, Any] = {"audio": {"url": ticket["fileKey"]}}
    if language:
        payload["language"] = language
    if context:
        payload["context"] = context
    payload["fileName"] = derived_name
    body = request_json("POST", "/stt/tasks", api_key, json=payload)
    return body["taskId"]


def submit_ocr_task_from_url(
    api_key: str,
    url: str,
    *,
    tier: str,
    prompt: str | None = None,
    file_name: str | None = None,
) -> str:
    """PDF URL→任务：流式下载（≤200MB）→ 签名 → OSS 直传 → 提交，返回 taskNo。"""
    derived_name = _derive_file_name(url, file_name, "document.pdf")
    extension = os.path.splitext(derived_name)[1].lower()
    if extension != ".pdf":
        raise SuanlinfangApiError(
            400,
            f"异步识别仅支持 PDF（收到 {extension or '(无扩展名)'}）；单张图片请直接用 recognize_image",
            retryable=False,
        )
    with tempfile.TemporaryDirectory(prefix="suanlinfang-ocr-") as tmp_dir:
        local_path = os.path.join(tmp_dir, derived_name)
        size_bytes = stream_to_file(url, local_path, OCR_PDF_MAX_BYTES)
        with open(local_path, "rb") as pdf_file:
            ticket = request_upload_ticket(api_key, "ocr", derived_name, size_bytes)
            put_bytes(ticket["uploadUrl"], pdf_file, ticket.get("headers") or {})
    payload: dict[str, Any] = {"tier": tier, "fileKey": ticket["fileKey"], "fileName": derived_name}
    if prompt:
        payload["prompt"] = prompt
    body = request_json("POST", "/ocr/tasks", api_key, json=payload)
    return body["taskId"]
