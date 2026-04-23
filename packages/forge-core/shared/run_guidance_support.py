from __future__ import annotations

import re
import subprocess
import time
from collections import deque
from pathlib import Path
from threading import Lock, Thread

from common import excerpt_text


READINESS_PATTERNS = (
    re.compile(r"\bready\b", re.IGNORECASE),
    re.compile(r"\blistening on\b", re.IGNORECASE),
    re.compile(r"\brunning on\b", re.IGNORECASE),
    re.compile(r"\bserver started\b", re.IGNORECASE),
    re.compile(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0)[:/\w.-]*", re.IGNORECASE),
)

BUILD_HINTS = (
    "build",
    "compile",
    "bundle",
    "assemble",
    "pack",
    "tsc",
)

SERVE_HINTS = (
    "serve",
    "start",
    "dev",
    "preview",
    "watch",
    "localhost",
    "0.0.0.0",
)

DEPLOY_HINTS = (
    "deploy",
    "release",
    "publish",
    "ship",
    "wrangler",
    "vercel",
    "netlify",
    "flyctl",
)

CAPTURE_LIMIT_CHARS = 12000
READINESS_CONTEXT_CHARS = 512


def detect_readiness(output: str) -> bool:
    if not output.strip():
        return False
    return any(pattern.search(output) for pattern in READINESS_PATTERNS)


def hint_in_text(text: str, hint: str) -> bool:
    pattern = r"(?<![a-z0-9]){0}(?![a-z0-9])".format(re.escape(hint))
    return re.search(pattern, text, re.IGNORECASE) is not None


def classify_command_kind(command: list[str], combined_output: str, readiness_detected: bool) -> str:
    haystack = " ".join(part.casefold() for part in command)
    output = combined_output.casefold()
    if any(hint_in_text(haystack, hint) or hint_in_text(output, hint) for hint in DEPLOY_HINTS):
        return "deploy"
    if readiness_detected or any(hint_in_text(haystack, hint) for hint in SERVE_HINTS):
        return "serve"
    if any(hint_in_text(haystack, hint) or hint_in_text(output, hint) for hint in BUILD_HINTS):
        return "build"
    if "build completed successfully" in output:
        return "build"
    return "generic"


class StreamBuffer:
    def __init__(self, limit_chars: int = CAPTURE_LIMIT_CHARS) -> None:
        self._chunks: deque[str] = deque()
        self._carry = ""
        self._limit_chars = limit_chars
        self._size = 0
        self._lock = Lock()
        self.readiness_detected = False

    def append(self, chunk: str) -> None:
        if not chunk:
            return
        with self._lock:
            probe = f"{self._carry}{chunk}"
            if detect_readiness(probe):
                self.readiness_detected = True
            self._carry = probe[-READINESS_CONTEXT_CHARS:]
            self._chunks.append(chunk)
            self._size += len(chunk)
            self._trim_to_limit()

    def text(self) -> str:
        with self._lock:
            return "".join(self._chunks)

    def _trim_to_limit(self) -> None:
        while self._size > self._limit_chars and self._chunks:
            overflow = self._size - self._limit_chars
            head = self._chunks[0]
            if len(head) <= overflow:
                self._chunks.popleft()
                self._size -= len(head)
                continue
            self._chunks[0] = head[overflow:]
            self._size -= overflow


def _drain_stream(stream, capture: StreamBuffer) -> None:
    try:
        while True:
            chunk = stream.read(4096)
            if not chunk:
                return
            capture.append(chunk)
    finally:
        stream.close()


def execute_command(command: list[str], workspace: Path, timeout_ms: int) -> dict:
    start = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=str(workspace),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    stdout_capture = StreamBuffer()
    stderr_capture = StreamBuffer()
    stdout_thread = Thread(target=_drain_stream, args=(process.stdout, stdout_capture), daemon=True)
    stderr_thread = Thread(target=_drain_stream, args=(process.stderr, stderr_capture), daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    timed_out = False
    try:
        exit_code = process.wait(timeout=timeout_ms / 1000)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        process.wait()
        exit_code = None

    stdout_thread.join()
    stderr_thread.join()
    duration_ms = int((time.perf_counter() - start) * 1000)
    stdout = stdout_capture.text()
    stderr = stderr_capture.text()
    return {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_ms": duration_ms,
        "readiness_detected": stdout_capture.readiness_detected or stderr_capture.readiness_detected,
    }


def determine_guidance(command_kind: str, execution: dict, readiness_detected: bool) -> tuple[str, str, str]:
    if execution["timed_out"] and readiness_detected:
        return (
            "running",
            "test",
            "Service looks ready. Run a targeted smoke or API check while the process is healthy.",
        )

    if execution["timed_out"]:
        return (
            "timed-out",
            "debug",
            "Command timed out without a clear ready signal. Inspect the last output and debug the stall before retrying.",
        )

    if execution["exit_code"] != 0:
        return (
            "failed",
            "debug",
            "Use the failing command as the reproduction anchor, then debug the root cause before trying a broader fix.",
        )

    if command_kind == "deploy":
        return (
            "completed",
            "deploy",
            "Run post-deploy verification and confirm rollback readiness before calling the release complete.",
        )

    if command_kind == "serve":
        return (
            "completed",
            "test",
            "Service started cleanly. Run the nearest smoke or manual verification against the live entry point.",
        )

    if command_kind == "build":
        return (
            "completed",
            "test",
            "Build passed. Run the nearest targeted test or smoke check before claiming the slice is done.",
        )

    return (
        "completed",
        "test",
        "Command completed. Validate the outcome with the nearest targeted verification before moving on.",
    )


def build_evidence(command_display: str, execution: dict, workspace: Path) -> list[str]:
    evidence = [
        f"workspace: {workspace}",
        f"command: {command_display}",
        f"duration_ms: {execution['duration_ms']}",
    ]
    if execution["stdout"].strip():
        evidence.append(f"stdout: {excerpt_text(execution['stdout'])}")
    if execution["stderr"].strip():
        evidence.append(f"stderr: {excerpt_text(execution['stderr'])}")
    if execution["timed_out"]:
        evidence.append("timeout: command exceeded the requested timeout budget")
    return evidence
