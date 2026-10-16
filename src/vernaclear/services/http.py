from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from vernaclear.core.models import ServiceError


def post_json(
    url: str,
    payload: Any,
    headers: dict[str, str] | None = None,
    timeout: float = 45.0,
) -> Any:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request_headers = {"Content-Type": "application/json", "User-Agent": "Vernaclear/0.1"}
    request_headers.update(headers or {})
    request = urllib.request.Request(url, data=body, headers=request_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:800]
        raise ServiceError(f"翻译服务返回 HTTP {error.code}：{detail}") from error
    except urllib.error.URLError as error:
        raise ServiceError(f"无法连接翻译服务：{error.reason}") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ServiceError("翻译服务返回了无法解析的数据。") from error


def post_form(
    url: str,
    fields: dict[str, str],
    headers: dict[str, str] | None = None,
    timeout: float = 45.0,
) -> Any:
    import urllib.parse

    body = urllib.parse.urlencode(fields).encode("utf-8")
    request_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Vernaclear/0.1",
    }
    request_headers.update(headers or {})
    request = urllib.request.Request(url, data=body, headers=request_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:800]
        raise ServiceError(f"翻译服务返回 HTTP {error.code}：{detail}") from error
    except urllib.error.URLError as error:
        raise ServiceError(f"无法连接翻译服务：{error.reason}") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ServiceError("翻译服务返回了无法解析的数据。") from error

