"""Optional durable storage of finished Shorts in Google Cloud Storage.

Local disk stays the working area (FFmpeg needs real files). When GCS_BUCKET is
set, every finished render, thumbnail and ZIP is also uploaded to
  gs://<bucket>/<same relative path as on disk>
and /api/files transparently restores a file from the bucket if the local copy
is gone (VM rebuilt, disk cleaned, preemptible instance replaced...).

Authentication is Application Default Credentials: on a Google Cloud VM attach
a service account with "Storage Object Admin" on the bucket — no key file needed.
Elsewhere set GOOGLE_APPLICATION_CREDENTIALS to a key file path.

Uploading is best-effort: a failed upload is logged and never fails a render.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger("shortforge.storage")


class RemoteStore:
    def __init__(self, bucket: str | None = None, client: Any | None = None) -> None:
        self.bucket_name = bucket if bucket is not None else os.environ.get("GCS_BUCKET", "").strip()
        self._client = client
        self._bucket: Any | None = None
        self.last_error: str | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.bucket_name)

    def _get_bucket(self) -> Any:
        if self._bucket is None:
            if self._client is None:
                from google.cloud import storage  # imported lazily: optional dependency

                self._client = storage.Client()
            self._bucket = self._client.bucket(self.bucket_name)
        return self._bucket

    def upload(self, local: Path, rel: str) -> bool:
        if not self.enabled or not local.is_file():
            return False
        try:
            self._get_bucket().blob(rel).upload_from_filename(str(local))
            self.last_error = None
            return True
        except Exception as exc:  # network, permission, quota ... never break rendering
            self.last_error = f"{type(exc).__name__}: {exc}"[:300]
            log.warning("GCS upload failed for %s: %s", rel, self.last_error)
            return False

    def restore(self, rel: str, local: Path) -> bool:
        """Download rel into local if the bucket has it."""
        if not self.enabled:
            return False
        try:
            blob = self._get_bucket().blob(rel)
            if not blob.exists():
                return False
            local.parent.mkdir(parents=True, exist_ok=True)
            tmp = local.with_name(local.name + ".part")
            blob.download_to_filename(str(tmp))
            tmp.replace(local)
            return True
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"[:300]
            log.warning("GCS restore failed for %s: %s", rel, self.last_error)
            return False

    def delete_prefix(self, prefix: str) -> int:
        if not self.enabled:
            return 0
        removed = 0
        try:
            for blob in self._get_bucket().list_blobs(prefix=prefix):
                blob.delete()
                removed += 1
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"[:300]
            log.warning("GCS delete failed for %s: %s", prefix, self.last_error)
        return removed

    def check(self) -> dict[str, Any]:
        """Used by the system status page. Never raises."""
        if not self.enabled:
            return {"backend": "local disk", "ok": True}
        try:
            ok = bool(self._get_bucket().exists())
            return {"backend": f"gcs:{self.bucket_name}", "ok": ok,
                    **({} if ok else {"error": "Bucket not found or no access."})}
        except Exception as exc:
            return {"backend": f"gcs:{self.bucket_name}", "ok": False,
                    "error": f"{type(exc).__name__}: {exc}"[:200]}


remote = RemoteStore()
