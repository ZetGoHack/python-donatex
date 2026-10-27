import httpx

from .auth import AuthType
from . import errors

_STATUS_ERRORS: dict[int, type[errors.ApiError]] = {
    400: errors.BadRequestError,
    401: errors.UnauthorizedError,
    403: errors.ForbiddenError,
    404: errors.NotFoundError,
    405: errors.MethodNotAllowedError,
    409: errors.ConflictError,
    415: errors.UnsupportedMediaTypeError,
}

_DEFAULT_MESSAGES = {
    401: "Токен отсутствует, просрочен, отозван или перевыпущен",
    403: "У токена нет нужного scope для этого метода",
    404: "Объект или путь не найден",
    405: "Метод HTTP не поддерживается для этого пути",
}


def _error_from_response(resp: "httpx.Response") -> errors.ApiError:
    status = resp.status_code
    message = resp.text.strip()
    field_errors = None
    trace_id = None

    try:
        body = resp.json()
    except ValueError:
        body = None

    if isinstance(body, dict):
        if isinstance(body.get("errors"), dict):
            field_errors = {
                str(k): [str(m) for m in (v if isinstance(v, list) else [v])]
                for k, v in body["errors"].items()
            }
            details = "; ".join(
                f"{field}: {', '.join(msgs)}" for field, msgs in field_errors.items()
            )
            message = details or body.get("title") or message
        elif body.get("error"):
            message = str(body["error"])
        elif body.get("title"):
            message = str(body["title"])
        trace_id = body.get("traceId")

    if not message:
        message = _DEFAULT_MESSAGES.get(status) or f"HTTP {status}"

    kwargs = {"status_code": status, "errors": field_errors, "trace_id": trace_id}

    if status == 429:
        try:
            retry_after = float(resp.headers.get("Retry-After", 1))
        except ValueError:
            retry_after = 1.0
        return errors.FloodWaitError(message, retry_after=retry_after, **kwargs)
    if status >= 500:
        return errors.ServerError(message, **kwargs)

    return _STATUS_ERRORS.get(status, errors.ApiError)(message, **kwargs)


class Transport:
    def __init__(self, auth: AuthType, proxy: str | None = None):
        self._auth = auth
        self._proxy = proxy
        self.is_ready = False
        self._client = None

    async def start(self):
        headers = {
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(
            headers=headers, trust_env=False, proxy=self._proxy
        )
        self.is_ready = True
        return self.is_ready

    async def stop(self):
        if self._client:
            await self._client.aclose()

        self._client = None
        self.is_ready = False

    async def _get_headers(self) -> dict:
        if not self._auth.is_authorized():
            raise errors.AuthRequiredError(
                "Клиент не авторизован. Для OAuth сначала вызовите client.authorize(code)"
            )
        token = await self._auth.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
        }

    async def _token_request(self, url: str, data: dict) -> dict:
        if not self.is_ready:
            raise errors.TransportNotReadyError(
                "Транспорт не готов вызывать запросы к API"
            )
        resp = await self._client.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 200:
            raise _error_from_response(resp)

        return resp.json()

    async def _request(self, method: str, url: str, **kwargs) -> "httpx.Response":
        if not self.is_ready:
            raise errors.TransportNotReadyError(
                "Транспорт не готов вызывать запросы к API"
            )
        headers = await self._get_headers()

        return await getattr(self._client, method)(url, headers=headers, **kwargs)

    async def _get(self, url: str, **kwargs):
        resp = await self._request("get", url, **kwargs)
        if resp.status_code != 200:
            raise _error_from_response(resp)

        return resp.json()

    async def _post(self, url: str, **kwargs):
        resp = await self._request("post", url, **kwargs)
        if resp.status_code not in (200, 204):
            raise _error_from_response(resp)
        if resp.status_code == 204 or not resp.content:
            return None

        return resp.json()

    async def _delete(self, url: str, **kwargs):
        resp = await self._request("delete", url, **kwargs)
        if resp.status_code != 204:
            raise _error_from_response(resp)

        return None
