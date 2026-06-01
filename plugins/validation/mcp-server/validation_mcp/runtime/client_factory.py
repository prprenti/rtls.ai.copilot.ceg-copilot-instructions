from __future__ import annotations

from collections import OrderedDict
from functools import lru_cache
import hashlib
from threading import Lock
from typing import TYPE_CHECKING, Any

from validation_mcp.settings import Settings

if TYPE_CHECKING:
    from backends.vmanager import VmanagerBackendUnavailable, VmanagerClient


@lru_cache(maxsize=1)
def _load_vmanager_types() -> tuple[type["VmanagerClient"], type["VmanagerBackendUnavailable"]]:
    from backends.vmanager import VmanagerBackendUnavailable, VmanagerClient

    return VmanagerClient, VmanagerBackendUnavailable


def _build_vamp_factory(settings: Settings):
    def factory() -> Any:
        from vamp.vamp import Vamp
        from vamp.vapi import VapiRequests

        request_kwargs: dict[str, Any] = {}
        if settings.api_base_path is not None:
            request_kwargs["api_base_path"] = settings.api_base_path
        if settings.username is not None:
            request_kwargs["username"] = settings.username
        if settings.password is not None:
            request_kwargs["password"] = settings.password
        if settings.token_path is not None:
            request_kwargs["token_path"] = settings.token_path
        if settings.verify is not None:
            request_kwargs["verify"] = settings.verify

        requests_client = VapiRequests(**request_kwargs)
        return Vamp(requests_client)

    return factory


def _new_vmanager_client(settings: Settings) -> "VmanagerClient":
    VmanagerClient, _ = _load_vmanager_types()
    return VmanagerClient(
        repo_root=settings.repo_root,
        vamp_factory=_build_vamp_factory(settings),
    )


def _secret_fingerprint(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _client_cache_key(settings: Settings) -> tuple[str | None, ...]:
    return (
        settings.repo_root,
        settings.api_base_path,
        settings.username,
        _secret_fingerprint(settings.password),
        _secret_fingerprint(settings.token_path),
        None if settings.verify is None else str(settings.verify),
    )


_CLIENT_CACHE: OrderedDict[tuple[str | None, ...], "VmanagerClient"] = OrderedDict()
_CLIENT_CACHE_LOCK = Lock()
_CLIENT_CACHE_SIZE = 4


def _cached_client(settings: Settings) -> "VmanagerClient":
    # Internal-only experiment: do not enable this for production traffic until
    # Vamp client thread-safety is verified for concurrent asyncio.to_thread use.
    cache_key = _client_cache_key(settings)
    with _CLIENT_CACHE_LOCK:
        cached = _CLIENT_CACHE.get(cache_key)
        if cached is not None:
            _CLIENT_CACHE.move_to_end(cache_key)
            return cached

    client = _new_vmanager_client(settings)

    with _CLIENT_CACHE_LOCK:
        cached = _CLIENT_CACHE.get(cache_key)
        if cached is not None:
            _CLIENT_CACHE.move_to_end(cache_key)
            return cached
        _CLIENT_CACHE[cache_key] = client
        _CLIENT_CACHE.move_to_end(cache_key)
        while len(_CLIENT_CACHE) > _CLIENT_CACHE_SIZE:
            _CLIENT_CACHE.popitem(last=False)

    return client


def get_vmanager_client(settings: Settings) -> "VmanagerClient":
    if settings.enable_client_cache:
        return _cached_client(settings)
    return _new_vmanager_client(settings)


def clear_client_cache() -> None:
    with _CLIENT_CACHE_LOCK:
        _CLIENT_CACHE.clear()