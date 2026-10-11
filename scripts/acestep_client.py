#!/usr/bin/env python3
"""Submit a vocabulary-song specification to an ACE-Step 1.5 API server."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from validate_spec import load_spec, validate


def request_json(url: str, payload: dict | None = None, token: str = "", timeout: int = 60) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))
    if isinstance(result, dict) and result.get("code") not in (None, 200):
        raise RuntimeError(result.get("error") or f"ACE-Step returned code {result.get('code')}")
    return result


def lyrics_text(spec: dict) -> str:
    blocks = []
    for section in spec["sections"]:
        blocks.append(f"[{section['name']}]\n" + "\n".join(section["lines"]))
    return "\n\n".join(blocks)


def generation_prompt(spec: dict) -> str:
    arrangement = spec["arrangement"]
    vocal = spec["vocal"]
    instruments = ", ".join(arrangement["instruments"])
    return (
        f"{spec['style_prompt']}. "
        f"Instrumentation and roles: {instruments}. "
        f"Arrangement arc: {arrangement['arc']}. "
        f"Vocal format: {vocal['format']}. Vocal timbre: {vocal['timbre']}. "
        f"Accent: {vocal['accent']}. Diction: {vocal['diction']}. "
        f"Delivery: {vocal['delivery']}. "
        "The supplied lyrics must be audibly sung with melody. Keep the lead vocal prominent. "
        "Avoid robotic text-to-speech, buried vocals, excessive melisma, heavy reverb, and long instrumental intros."
    )


def download(url: str, target: Path, token: str) -> None:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=300) as response, target.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)


def run(spec: dict, server: str, out_dir: Path, token: str, timeout: int, thinking: bool) -> None:
    server = server.rstrip("/")
    request_json(f"{server}/health", token=token, timeout=30)
    payload = {
        "prompt": generation_prompt(spec),
        "lyrics": lyrics_text(spec),
        "thinking": thinking,
        "vocal_language": "en",
        "audio_format": "wav",
        "bpm": spec["bpm"],
        "key_scale": spec["key"],
        "time_signature": "4",
        "audio_duration": spec["duration_seconds"],
        "inference_steps": 8,
        "batch_size": 1,
        "use_cot_caption": False,
        "use_cot_language": False,
    }
    submitted = request_json(f"{server}/release_task", payload, token, timeout=120)
    task_id = submitted.get("data", {}).get("task_id")
    if not task_id:
        raise RuntimeError(f"ACE-Step did not return a task_id: {submitted}")
    print(f"Submitted ACE-Step task {task_id}")

    deadline = time.monotonic() + timeout
    final_item = None
    while time.monotonic() < deadline:
        status_response = request_json(
            f"{server}/query_result", {"task_id_list": [task_id]}, token, timeout=120
        )
        items = status_response.get("data") or []
        if items:
            item = items[0]
            status = int(item.get("status", 0))
            if status == 1:
                final_item = item
                break
            if status == 2:
                raise RuntimeError(item.get("error") or "ACE-Step generation failed")
        time.sleep(5)
    if final_item is None:
        raise TimeoutError(f"ACE-Step task did not finish within {timeout} seconds")

    raw_result = final_item.get("result", "[]")
    results = json.loads(raw_result) if isinstance(raw_result, str) else raw_result
    if isinstance(results, dict):
        results = [results]
    if not results:
        raise RuntimeError("ACE-Step task succeeded but returned no audio")

    out_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for index, item in enumerate(results, start=1):
        relative = item.get("url") or item.get("file")
        if not relative:
            continue
        audio_url = relative if relative.startswith(("http://", "https://")) else urllib.parse.urljoin(server + "/", relative.lstrip("/"))
        suffix = Path(urllib.parse.urlparse(audio_url).path).suffix or ".wav"
        target = out_dir / f"full-song-{index}{suffix}"
        download(audio_url, target, token)
        downloaded.append(str(target))
    if not downloaded:
        raise RuntimeError("ACE-Step returned results but no downloadable audio URL")

    report = {
        "backend": "ACE-Step-1.5",
        "server": server,
        "task_id": task_id,
        "thinking": thinking,
        "files": downloaded,
        "result": results,
    }
    (out_dir / "acestep-result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Downloaded {len(downloaded)} ACE-Step audio file(s) to {out_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--server", default="http://127.0.0.1:8001")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--thinking", action="store_true", help="Use the optional ACE-Step language model")
    args = parser.parse_args()
    spec = load_spec(args.spec.resolve())
    errors, warnings = validate(spec)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        raise SystemExit("\n".join(f"ERROR: {error}" for error in errors))
    token = os.environ.get("ACESTEP_API_KEY", "")
    try:
        run(spec, args.server, args.out.resolve(), token, args.timeout, args.thinking)
    except (urllib.error.URLError, OSError, RuntimeError, TimeoutError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
