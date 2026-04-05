from __future__ import annotations

import os
import subprocess
import threading
from typing import Any


def is_kreg_cuda_mode(config: dict[str, Any]) -> bool:
    training_cfg = config.get("training", {})
    model_type = str(training_cfg.get("ml_model_type", "")).strip().casefold()
    device = str(training_cfg.get("device", "")).strip().casefold()
    return model_type == "kreg" and device.startswith("cuda")


class GPUMonitor:
    """Poll nvidia-smi and track whether the current training process used GPU."""

    def __init__(self, *, enabled: bool, poll_interval_seconds: float = 2.0) -> None:
        self.enabled = bool(enabled)
        self.poll_interval_seconds = max(0.5, float(poll_interval_seconds))
        self.root_pid = os.getpid()
        self.samples = 0
        self.gpu_observed = False
        self.gpu_max_memory_mb = 0
        self.gpu_poll_errors = 0
        self.last_error: str | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if not self.enabled:
            return
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="gpu-monitor", daemon=True)
        self._thread.start()

    def stop(self) -> dict[str, Any]:
        if self._thread is not None:
            self._stop_event.set()
            self._thread.join(timeout=self.poll_interval_seconds * 3)
        with self._lock:
            return {
                "gpu_monitor_enabled": self.enabled,
                "gpu_observed": self.gpu_observed,
                "gpu_max_memory_mb": self.gpu_max_memory_mb,
                "samples": self.samples,
                "gpu_poll_errors": self.gpu_poll_errors,
                "gpu_monitor_last_error": self.last_error,
                "gpu_monitored_root_pid": self.root_pid,
            }

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._poll_once()
            self._stop_event.wait(self.poll_interval_seconds)

    def _poll_once(self) -> None:
        try:
            process_rows = self._query_compute_apps()
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self.gpu_poll_errors += 1
                self.last_error = f"{type(exc).__name__}: {exc}"
            return

        tracked_pids = self._collect_descendant_pids(self.root_pid)
        tracked_pids.add(self.root_pid)

        observed = False
        peak = 0
        for row in process_rows:
            pid = row.get("pid")
            used_memory_mb = row.get("used_memory_mb", 0)
            if pid in tracked_pids:
                observed = True
                if used_memory_mb > peak:
                    peak = used_memory_mb

        with self._lock:
            self.samples += 1
            if observed:
                self.gpu_observed = True
                if peak > self.gpu_max_memory_mb:
                    self.gpu_max_memory_mb = peak

    @staticmethod
    def _query_compute_apps() -> list[dict[str, int]]:
        result = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise RuntimeError(stderr or f"nvidia-smi returned {result.returncode}")

        rows: list[dict[str, int]] = []
        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if "No running processes found" in line:
                continue
            if "," not in line:
                continue
            pid_text, used_memory_text = [part.strip() for part in line.split(",", 1)]
            if not pid_text or not used_memory_text:
                continue
            try:
                pid = int(pid_text)
                used_memory_mb = int(used_memory_text)
            except ValueError:
                continue
            rows.append({"pid": pid, "used_memory_mb": used_memory_mb})
        return rows

    @staticmethod
    def _collect_descendant_pids(root_pid: int) -> set[int]:
        """Collect descendant pids using `ps`; fall back to an empty set when unavailable."""

        try:
            result = subprocess.run(
                ["ps", "-eo", "pid=,ppid="],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception:  # noqa: BLE001
            return set()

        if result.returncode != 0:
            return set()

        parent_to_children: dict[int, set[int]] = {}
        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2:
                continue
            try:
                pid = int(parts[0])
                ppid = int(parts[1])
            except ValueError:
                continue
            parent_to_children.setdefault(ppid, set()).add(pid)

        descendants: set[int] = set()
        queue = [root_pid]
        while queue:
            current = queue.pop()
            for child in parent_to_children.get(current, set()):
                if child in descendants:
                    continue
                descendants.add(child)
                queue.append(child)
        return descendants
