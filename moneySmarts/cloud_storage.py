import os
import json
import base64
import pickle
import logging
from typing import Optional, Any, Dict

try:
    import requests  # type: ignore
except Exception:  # keep optional until installed
    requests = None  # type: ignore


class StorageBackend:
    """Abstract storage backend for saving/loading game state."""

    def save(self, data: Dict[str, Any], filename: str = "savegame.dat") -> None:
        raise NotImplementedError

    def load(self, filename: str = "savegame.dat") -> Optional[Dict[str, Any]]:
        raise NotImplementedError


class LocalFileStorage(StorageBackend):
    def save(self, data: Dict[str, Any], filename: str = "savegame.dat") -> None:
        # Preserve existing behavior (binary pickle to file)
        with open(filename, 'wb') as f:
            pickle.dump(data, f)

    def load(self, filename: str = "savegame.dat") -> Optional[Dict[str, Any]]:
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            return None
        with open(filename, 'rb') as f:
            return pickle.load(f)


class FirebaseStorage(StorageBackend):
    """
    Minimal Firebase Realtime Database REST client.

    Configuration via environment variables:
      - FIREBASE_DB_URL: base URL of the RTDB, e.g. https://your-project-id.firebaseio.com
      - FIREBASE_PATH: path under which to store saves (default: /moneySmarts/saves)
      - FIREBASE_AUTH_TOKEN: optional auth token (user ID token or database secret)
      - CLOUD_SAVE_KEY: logical key for the save (default: "default"). You can
                        still pass filename; we'll derive a key from it if given.
    """

    def __init__(self):
        if requests is None:
            raise RuntimeError("requests is required for FirebaseStorage; install it via requirements.txt")
        self.db_url = os.getenv("FIREBASE_DB_URL")
        if not self.db_url:
            raise RuntimeError("FIREBASE_DB_URL not set")
        self.base_path = os.getenv("FIREBASE_PATH", "/moneySmarts/saves")
        self.auth_token = os.getenv("FIREBASE_AUTH_TOKEN")
        # timeout seconds for HTTP
        self.timeout = float(os.getenv("FIREBASE_TIMEOUT", "8"))

    def _key_from_filename(self, filename: str) -> str:
        # Convert filename like savegame.dat or savegame_slot1.dat to keys
        key = os.getenv("CLOUD_SAVE_KEY")
        if key:
            return key
        base = os.path.basename(filename)
        name, _ext = os.path.splitext(base)
        # sanitize to RTDB key-safe (avoid dots and slashes)
        return name.replace('.', '_').replace('/', '_').replace('\\', '_')

    def _url(self, key: str) -> str:
        # Ensure single leading slash for base_path
        path = self.base_path if self.base_path.startswith('/') else '/' + self.base_path
        # Append key.json
        return f"{self.db_url}{path}/{key}.json"

    def save(self, data: Dict[str, Any], filename: str = "savegame.dat") -> None:
        key = self._key_from_filename(filename)
        # Encode the pickle as base64 string to keep it JSON friendly
        raw = pickle.dumps(data)
        b64 = base64.b64encode(raw).decode('utf-8')
        payload = {"blob": b64}
        params = {}
        if self.auth_token:
            params["auth"] = self.auth_token
        url = self._url(key)
        try:
            resp = requests.put(url, params=params, json=payload, timeout=self.timeout)
            resp.raise_for_status()
        except Exception as e:
            logging.error(f"Firebase save failed: {e}")
            raise

    def load(self, filename: str = "savegame.dat") -> Optional[Dict[str, Any]]:
        key = self._key_from_filename(filename)
        params = {}
        if self.auth_token:
            params["auth"] = self.auth_token
        url = self._url(key)
        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logging.error(f"Firebase load failed: {e}")
            raise
        if not data or "blob" not in data or not data["blob"]:
            return None
        try:
            raw = base64.b64decode(data["blob"])  # type: ignore[arg-type]
            return pickle.loads(raw)
        except Exception as e:
            logging.error(f"Corrupt Firebase save blob: {e}")
            return None


_storage_singleton: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    global _storage_singleton
    if _storage_singleton is not None:
        return _storage_singleton

    backend = os.getenv("CLOUD_BACKEND", "auto").lower()
    if backend not in ("auto", "firebase", "local"):
        backend = "auto"

    # Auto selection: if FIREBASE_DB_URL is set, prefer Firebase; else local
    if backend == "firebase" or (backend == "auto" and os.getenv("FIREBASE_DB_URL")):
        try:
            _storage_singleton = FirebaseStorage()
            logging.info("Using FirebaseStorage backend")
            return _storage_singleton
        except Exception as e:
            logging.warning(f"Falling back to LocalFileStorage: {e}")

    _storage_singleton = LocalFileStorage()
    logging.info("Using LocalFileStorage backend")
    return _storage_singleton
