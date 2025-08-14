from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SecretProvider(Protocol):
    def get(self, key: str, default: str = "") -> str:  # pragma: no cover - protocol
        ...

rjgwergnweek
class AuthMethod(Enum):
    """Vault authentication methods."""
    TOKEN = "token"
    APPROLE = "approle"
    USERPASS = "userpass"
    LDAP = "ldap"
    KUBERNETES = "kubernetes"


@dataclass
class EnvSecretProvider:
    """Read secrets from environment variables with KEY_FILE override.

    Precedence: KEY_FILE (if set and readable) > KEY (if set) > default.
    """

    def get(self, key: str, default: str = "") -> str:
        file_key = f"{key}_FILE"
        file_path = os.getenv(file_key)
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except OSError as exc:  # pragma: no cover - IO error path
                raise RuntimeError(
                    f"Unable to read secret file for {key}: {file_path} ({exc})"
                ) from exc
        return os.getenv(key, default)


@dataclass
class VaultSecretProvider:
    """Fetch secrets from HashiCorp Vault (KV v2 recommended) with caching.

    If hvac is not installed or VAULT_ADDR/TOKEN are missing, raises at call-time.
    Path is constructed as: {mount}/{path_prefix}/{key}
    """

    addr: str | None = None
    token: str | None = None
    mount: str = "kv"
    path_prefix: str = "app"
    auth_method: AuthMethod = AuthMethod.TOKEN
    cache_ttl: int = 300  # 5 minutes default cache TTL
    _client: Optional[Any] = field(default=None, init=False)
    _cache: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)
    _cache_timestamps: Dict[str, float] = field(default_factory=dict, init=False)

    def __post_init__(self):
        """Check if hvac is available at initialization time."""
        try:
            import hvac  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "VaultSecretProvider requires 'hvac' package. Install and retry."
            ) from exc

    def _get_cache_key(self, key: str) -> str:
        """Generate a cache key for the secret."""
        return f"{self.auth_method.value}:{self.mount}:{self.path_prefix}:{key}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached secret is still valid."""
        if cache_key not in self._cache_timestamps:
            return False
        return time.time() - self._cache_timestamps[cache_key] < self.cache_ttl

    def _get_from_cache(self, key: str) -> Optional[str]:
        """Get secret from cache if valid."""
        cache_key = self._get_cache_key(key)
        if self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for secret: {key}")
            return self._cache[cache_key].get("value")
        return None

    def _set_cache(self, key: str, value: str) -> None:
        """Set secret in cache."""
        cache_key = self._get_cache_key(key)
        self._cache[cache_key] = {"value": value}
        self._cache_timestamps[cache_key] = time.time()
        logger.debug(f"Cached secret: {key}")

    def _client(self):  # pragma: no cover - optional dependency
        """Get authenticated Vault client."""
        if self._client is not None:
            return self._client

        # Check if hvac is available at import time, not just at call time
        try:
            import hvac  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "VaultSecretProvider requires 'hvac' package. Install and retry."
            ) from exc

        address = self.addr or os.getenv("VAULT_ADDR")
        if not address:
            raise RuntimeError("VAULT_ADDR not set")

        client = hvac.Client(url=address)

        # Authenticate based on the selected method
        if self.auth_method == AuthMethod.TOKEN:
            token = self.token or os.getenv("VAULT_TOKEN")
            if not token:
                raise RuntimeError("VAULT_TOKEN not set")
            client.token = token
        elif self.auth_method == AuthMethod.APPROLE:
            role_id = os.getenv("VAULT_ROLE_ID")
            secret_id = os.getenv("VAULT_SECRET_ID")
            if not role_id or not secret_id:
                raise RuntimeError("VAULT_ROLE_ID/VAULT_SECRET_ID not set")
            client.auth.approle.login(role_id=role_id, secret_id=secret_id)
        elif self.auth_method == AuthMethod.USERPASS:
            username = os.getenv("VAULT_USERNAME")
            password = os.getenv("VAULT_PASSWORD")
            if not username or not password:
                raise RuntimeError("VAULT_USERNAME/VAULT_PASSWORD not set")
            client.auth.userpass.login(username=username, password=password)
        elif self.auth_method == AuthMethod.KUBERNETES:
            jwt_token = os.getenv("VAULT_K8S_JWT")
            role = os.getenv("VAULT_K8S_ROLE")
            if not jwt_token or not role:
                raise RuntimeError("VAULT_K8S_JWT/VAULT_K8S_ROLE not set")
            client.auth.kubernetes.login(role=role, jwt=jwt_token)
        else:
            raise RuntimeError(f"Unsupported authentication method: {self.auth_method}")

        if not client.is_authenticated():
            raise RuntimeError("Vault authentication failed")

        self._client = client
        return client

    def get(self, key: str, default: str = "") -> str:
        """Get secret from Vault with caching support."""
        # Try to get from cache first
        cached_value = self._get_from_cache(key)
        if cached_value is not None:
            return cached_value

        # Not in cache or expired, fetch from Vault
        mount = os.getenv("VAULT_KV_MOUNT", self.mount)
        prefix = os.getenv("VAULT_PATH_PREFIX", self.path_prefix)
        path = f"{prefix}/{key.lower()}"
        
        try:
            client = self._client()  # pragma: no cover - optional path
            # KV v2 read
            resp = client.secrets.kv.v2.read_secret(
                mount_point=mount, path=path
            )
            data = resp.get("data", {}).get("data", {})
            # Expect the secret stored under the exact key name by convention
            value = str(data.get(key, data.get("value", default)))
            
            # Cache the value
            self._set_cache(key, value)
            
            return value
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - integration path
            logger.warning(f"Failed to fetch secret '{key}' from Vault: {exc}")
            return default

    def clear_cache(self) -> None:
        """Clear all cached secrets."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.debug("Cleared secret cache")

    def refresh_secret(self, key: str) -> Optional[str]:
        """Force refresh a specific secret from Vault."""
        # Remove from cache
        cache_key = self._get_cache_key(key)
        if cache_key in self._cache:
            del self._cache[cache_key]
        if cache_key in self._cache_timestamps:
            del self._cache_timestamps[cache_key]
        
        # Fetch fresh value
        return self.get(key)


def get_secret_provider() -> SecretProvider:
    """Get the configured secret provider."""
    backend = os.getenv("SECRETS_BACKEND", "env").lower()
    if backend == "vault":
        # Configure Vault provider based on environment variables
        auth_method_str = os.getenv("VAULT_AUTH_METHOD", "token").lower()
        try:
            auth_method = AuthMethod(auth_method_str)
        except ValueError:
            logger.warning(f"Invalid auth method '{auth_method_str}', defaulting to TOKEN")
            auth_method = AuthMethod.TOKEN
        
        cache_ttl = int(os.getenv("VAULT_CACHE_TTL", "300"))
        
        return VaultSecretProvider(
            addr=os.getenv("VAULT_ADDR"),
            token=os.getenv("VAULT_TOKEN"),
            mount=os.getenv("VAULT_KV_MOUNT", "kv"),
            path_prefix=os.getenv("VAULT_PATH_PREFIX", "app"),
            auth_method=auth_method,
            cache_ttl=cache_ttl
        )
    return EnvSecretProvider()


