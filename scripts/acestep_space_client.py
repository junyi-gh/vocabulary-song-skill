#!/usr/bin/env python3
"""Render a vocabulary song with the official ACE-Step 1.5 Hugging Face Space."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

try:
    from gradio_client import Client
except ImportError as exc:  # pragma: no cover - depends on the selected runtime
    raise SystemExit(
        "ERROR: gradio_client is required. Install it with: py -m pip install gradio_client"
    ) from exc

from acestep_client import generation_prompt, lyrics_text
from validate_spec import load_spec, validate


SPACE_ID = "ACE-Step/Ace-Step-v1.5"
API_NAME = "/generation_wrapper"
AUDIO_SUFFIXES = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}


def build_arguments(client: Client, spec: dict[str, Any], model: str, seed: str) -> list[Any]:
    endpoint = next(
        (item for item in client.endpoints.values() if item.api_name == API_NAME), None
    )
    if endpoint is None:
        raise RuntimeError(f"The Space does not expose {API_NAME}")

    parameters = endpoint.parameters_info
    if len(parameters) != 49:
        raise RuntimeError(
            f"ACE-Step Space interface changed: expected 49 inputs, found {len(parameters)}"
        )

    args: list[Any] = []
    for parameter in parameters:
        if parameter.get("parameter_has_default"):
            args.append(parameter.get("parameter_default"))
        else:
            args.append(None)

    # The public Space currently exposes generic labels for most controls, so these
    # stable positions are verified above before any paid or queued generation starts.
    overrides = {
        0: model,
        1: "custom",
        2: "",
        3: "en",
        4: generation_prompt(spec),
        5: lyrics_text(spec),
        6: spec["bpm"],
        7: spec["key"],
        8: "4",
        9: "en",
        10: 8,
        11: 7.0,
        12: False,
        13: seed,
        14: None,
        15: spec["duration_seconds"],
        16: 1,
        17: None,
        18: "",
        19: 0.0,
        20: -1,
        21: "Fill the audio semantic mask based on the given conditions:",
        22: 1.0,
        23: "text2music",
        24: False,
        25: 0.0,
        26: 1.0,
        27: 3.0,
        28: "ode",
        29: "",
        30: "mp3",
        31: 0.85,
        32: True,
        33: 2.0,
        34: 0,
        35: 0.9,
        36: "NO USER INPUT",
        37: True,
        38: True,
        39: True,
        40: False,
        41: True,
        42: False,
        43: False,
        44: 0.5,
        45: 8,
        46: "vocals",
        47: ["keyboard", "bass", "drums", "guitar", "strings", "backing_vocals", "vocals"],
        48: False,
    }
    for index, value in overrides.items():
        args[index] = value
    return args


def collect_audio_paths(value: Any) -> list[Path]:
    found: list[Path] = []

    def visit(item: Any) -> None:
        if isinstance(item, (str, os.PathLike)):
            path = Path(item)
            if path.suffix.lower() in AUDIO_SUFFIXES and path.is_file():
                found.append(path)
        elif isinstance(item, dict):
            for key in ("path", "name", "url"):
                if key in item:
                    visit(item[key])
            for nested in item.values():
                if isinstance(nested, (dict, list, tuple)):
                    visit(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                visit(nested)
        else:
            path_value = getattr(item, "path", None)
            if path_value:
                visit(path_value)

    visit(value)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in found:
        resolved = str(path.resolve())
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def serializable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, os.PathLike):
        return str(value)
    if isinstance(value, dict):
        return {str(key): serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(item) for item in value]
    if hasattr(value, "model_dump"):
        return serializable(value.model_dump())
    return repr(value)


def run(spec: dict[str, Any], out_dir: Path, model: str, seed: str, token: str) -> list[Path]:
    client = Client(SPACE_ID, token=token or None, verbose=False)
    args = build_arguments(client, spec, model, seed)
    print("Submitted to the official ACE-Step Space; waiting for a sung result...")
    result = client.predict(*args, api_name=API_NAME)
    audio_paths = collect_audio_paths(result)
    if not audio_paths:
        raise RuntimeError("ACE-Step returned no downloadable audio file")

    out_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for index, source in enumerate(audio_paths, start=1):
        target = out_dir / f"full-song-{index}{source.suffix.lower()}"
        shutil.copy2(source, target)
        copied.append(target)

    report = {
        "backend": "Official ACE-Step 1.5 Hugging Face Space",
        "space": SPACE_ID,
        "api_name": API_NAME,
        "model": model,
        "seed": seed,
        "prompt": generation_prompt(spec),
        "lyrics": lyrics_text(spec),
        "files": [str(path) for path in copied],
        "raw_result": serializable(result),
    }
    (out_dir / "acestep-space-result.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--model",
        choices=("acestep-v15-xl-turbo", "acestep-v15-turbo"),
        default="acestep-v15-xl-turbo",
    )
    parser.add_argument("--seed", default="20261011")
    args = parser.parse_args()

    spec = load_spec(args.spec.resolve())
    errors, warnings = validate(spec)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        raise SystemExit("\n".join(f"ERROR: {error}" for error in errors))

    token = os.environ.get("HF_TOKEN", "")
    try:
        files = run(spec, args.out.resolve(), args.model, args.seed, token)
    except Exception as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    for path in files:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
