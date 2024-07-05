from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar, cast

from httpx import Headers

__all__ = ['SparkError', 'SparkSdkError', 'SparkApiError', 'ErrorMessage']

TReq = TypeVar('TReq')
TResp = TypeVar('TResp')


class TRequest(Generic[TReq]):
    def __init__(self, url: str, method: str, headers: Headers, body: Optional[TReq]):
        self.url = url
        self.method = method
        self.headers = headers
        self.body = body


class TResponse(Generic[TResp]):
    def __init__(self, headers: Headers, body: TResp, raw: str):
        self.headers = headers
        self.body = body
        self.raw = raw


class SparkError(Exception):
    """Base class for all SDK-related errors."""

    def __init__(self, message: str, cause: Optional[Any] = None):
        super().__init__()
        self.name = self.__class__.__name__
        self.message = message
        self.cause = cause

    def __str__(self):
        error = f'{self.name}: {self.message}'
        return f'{error} ({self.details})' if self.details else error

    def __repr__(self):
        return f'<{self.name}>'

    def to_dict(self) -> Dict[str, Any]:
        return {'name': self.name, 'message': self.message, 'cause': self.cause}

    @property
    def details(self) -> str:
        if isinstance(self.cause, Exception):
            return str(self.cause)
        elif isinstance(self.cause, str):
            return self.cause
        elif isinstance(self.cause, dict):
            return str(self.cause)
        return ''

    @staticmethod
    def sdk(message: str, cause: Optional[Any] = None) -> SparkSdkError:
        return SparkSdkError(ErrorMessage(message, cause))

    @staticmethod
    def api(status: int, error: Dict[str, Any]) -> SparkApiError:
        return SparkApiError.when(status, ErrorMessage.from_dict(error))


class SparkSdkError(SparkError):
    """
    Base class for SDK-specific errors.

    Usually thrown when an argument fails to comply with the expected format.
    Because it's a client-side error, it will include in the majority of cases
    the invalid entry as `cause`.

    If the argument causes another process to fail, the `cause` will be referencing
    that thrown `Exception`. The `timestamp` helps to define a hierarchy of errors since
    the `cause` might be a `SparkError` as well.
    """

    def __init__(self, error: ErrorMessage):
        super().__init__(error.message, error.cause)
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), 'timestamp': self.timestamp}


class SparkApiError(SparkError):
    """
    Base class for errors related to the API.

    When attempting to communicate with the API, the SDK will wrap any sort of failure
    (any error during the round trip) into `SparkApiError`. The `status` is the HTTP
    status code of the response, and the `request_id`, a unique identifier of the request.
    """

    def __init__(self, error: ErrorMessage, status: Optional[int] = None):
        cause = ApiErrorCause.from_dict(error.cause) if isinstance(error.cause, dict) else None
        super().__init__(f"{status or ''} {error.message}".strip(), cause)
        self.status = status

    @property
    def request_id(self) -> str:
        if self.cause and isinstance(self.cause, ApiErrorCause):
            return self.cause.request.headers.get('x-request-id', '')
        return ''  # Note: this should never happen if thrown by the SDK

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), 'status': self.status}

    @staticmethod
    def when(status: int, error: ErrorMessage) -> SparkApiError:
        if status == 0:
            return InternetError(error, 0)
        elif status == 400:
            return BadRequestError(error, 400)
        elif status == 401:
            return UnauthorizedError(error, 401)
        elif status == 403:
            return ForbiddenError(error, 403)
        elif status == 404:
            return NotFoundError(error, 404)
        elif status == 409:
            return ConflictError(error, 409)
        elif status == 415:
            return UnsupportedMediaTypeError(error, 415)
        elif status == 422:
            return UnprocessableEntityError(error, 422)
        elif status == 429:
            return RateLimitError(error, 429)
        elif status == 500:
            return InternalServerError(error, 500)
        elif status == 503:
            return ServiceUnavailableError(error, 503)
        elif status == 504:
            return GatewayTimeoutError(error, 504)
        else:
            return UnknownApiError(error)


class InternetError(SparkApiError):
    status = 0


class BadRequestError(SparkApiError):
    status = 400


class UnauthorizedError(SparkApiError):
    status = 401


class ForbiddenError(SparkApiError):
    status = 403


class NotFoundError(SparkApiError):
    status = 404


class ConflictError(SparkApiError):
    status = 409


class UnsupportedMediaTypeError(SparkApiError):
    status = 415


class UnprocessableEntityError(SparkApiError):
    status = 422


class RateLimitError(SparkApiError):
    status = 429


class InternalServerError(SparkApiError):
    status = 500


class ServiceUnavailableError(SparkApiError):
    status = 503


class GatewayTimeoutError(SparkApiError):
    status = 504


class UnknownApiError(SparkApiError):
    status = None


class ErrorMessage:
    def __init__(self, message: str, cause: Optional[Any] = None):
        self.message = message
        self.cause = cause

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ErrorMessage:
        message = cast(str, data.get('message'))
        cause = cast(Optional[Any], data.get('cause'))
        return ErrorMessage(message, cause)


class ApiErrorCause(Generic[TReq, TResp]):
    def __init__(self, request: TRequest[TReq], response: Optional[TResponse[TResp]] = None):
        self.request = request
        self.response = response

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ApiErrorCause:
        req, res = cast(dict[str, Any], data.get('request')), data.get('response')
        request = TRequest(req['url'], req['method'], req['headers'], req['body'])
        if not res:
            return ApiErrorCause(request)
        return ApiErrorCause(request, TResponse(res['headers'], res['body'], res['raw']))
