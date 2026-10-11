#!/usr/bin/env python3
"""Build a lightweight speech-over-music rehearsal track on Windows."""

from __future__ import annotations

import argparse
import array
import json
import math
import random
import subprocess
import tempfile
import wave
from pathlib import Path

from validate_spec import load_spec, validate


SAMPLE_RATE = 44_100
MAX_I16 = 32_767
NOTE_NAMES = {"C": 60, "C#": 61, "DB": 61, "D": 62, "D#": 63, "EB": 63, "E": 64,
              "F": 65, "F#": 66, "GB": 66, "G": 67, "G#": 68, "AB": 68, "A": 69,
              "A#": 70, "BB": 70, "B": 71}


def midi_hz(note: int) -> float:
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def clamp(value: float) -> int:
    return max(-MAX_I16, min(MAX_I16, int(value)))


def add_tone(track: array.array, start: float, duration: float, frequency: float,
             volume: float, waveform: str = "sine", attack: float = 0.01,
             release: float = 0.08) -> None:
    first = max(0, int(start * SAMPLE_RATE))
    count = max(0, min(int(duration * SAMPLE_RATE), len(track) - first))
    for i in range(count):
        t = i / SAMPLE_RATE
        if waveform == "triangle":
            phase = (frequency * t) % 1.0
            raw = 4.0 * abs(phase - 0.5) - 1.0
        elif waveform == "square":
            raw = 1.0 if math.sin(2 * math.pi * frequency * t) >= 0 else -1.0
        else:
            raw = math.sin(2 * math.pi * frequency * t)
        env = min(1.0, t / max(attack, 1e-4), (duration - t) / max(release, 1e-4))
        track[first + i] = clamp(track[first + i] + raw * max(0.0, env) * volume * MAX_I16)


def add_noise(track: array.array, start: float, duration: float, volume: float,
              rng: random.Random) -> None:
    first = max(0, int(start * SAMPLE_RATE))
    count = max(0, min(int(duration * SAMPLE_RATE), len(track) - first))
    for i in range(count):
        env = math.exp(-8.0 * i / max(count, 1))
        track[first + i] = clamp(track[first + i] + rng.uniform(-1, 1) * env * volume * MAX_I16)


def synth_backing(duration: float, bpm: int, key: str) -> array.array:
    total = int(duration * SAMPLE_RATE)
    track = array.array("h", [0]) * total
    beat = 60.0 / bpm
    root_name = key.strip().split()[0].upper().replace("♭", "B").replace("♯", "#")
    root = NOTE_NAMES.get(root_name, 60)
    progression = [0, 7, 9, 5]  # I–V–vi–IV roots in semitones
    chord_quality = [(0, 4, 7), (0, 4, 7), (0, 3, 7), (0, 4, 7)]
    rng = random.Random(20261011)
    bar = 0
    while bar * beat * 4 < duration:
        bar_start = bar * beat * 4
        chord_index = bar % len(progression)
        chord_root = root + progression[chord_index]
        for semitone in chord_quality[chord_index]:
            add_tone(track, bar_start, beat * 3.8, midi_hz(chord_root + semitone), 0.045, "sine", 0.08, 0.25)
        for beat_index in range(4):
            t = bar_start + beat_index * beat
            if beat_index in (0, 2):
                add_tone(track, t, 0.14, 62.0, 0.16, "sine", 0.002, 0.12)
            else:
                add_noise(track, t, 0.11, 0.09, rng)
            add_tone(track, t, beat * 0.42, midi_hz(chord_root - 12), 0.08, "triangle", 0.005, 0.08)
            add_noise(track, t, 0.025, 0.025, rng)
            add_noise(track, t + beat / 2, 0.02, 0.018, rng)
        bar += 1
    return track


def write_wav(path: Path, samples: array.array) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(samples.tobytes())


def read_wav_mono(path: Path) -> tuple[array.array, int]:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        rate = handle.getframerate()
        raw = handle.readframes(handle.getnframes())
    if width != 2:
        raise RuntimeError(f"Unsupported speech WAV sample width: {width}")
    values = array.array("h")
    values.frombytes(raw)
    if channels == 2:
        values = array.array("h", ((values[i] + values[i + 1]) // 2 for i in range(0, len(values), 2)))
    elif channels != 1:
        raise RuntimeError(f"Unsupported speech WAV channel count: {channels}")
    return values, rate


def resample(samples: array.array, source_rate: int) -> array.array:
    if source_rate == SAMPLE_RATE:
        return samples
    out_len = int(len(samples) * SAMPLE_RATE / source_rate)
    if not samples or out_len <= 0:
        return array.array("h")
    output = array.array("h", [0]) * out_len
    scale = source_rate / SAMPLE_RATE
    for i in range(out_len):
        pos = i * scale
        left = min(int(pos), len(samples) - 1)
        right = min(left + 1, len(samples) - 1)
        fraction = pos - left
        output[i] = clamp(samples[left] * (1 - fraction) + samples[right] * fraction)
    return output


def mix(track: array.array, clip: array.array, start: float, gain: float = 0.85) -> None:
    first = int(start * SAMPLE_RATE)
    for i, value in enumerate(clip):
        index = first + i
        if index >= len(track):
            break
        track[index] = clamp(track[index] + value * gain)


def speak(text: str, output: Path, rate: int = 0) -> None:
    script = Path(__file__).with_name("sapi_tts.ps1")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as handle:
        handle.write(text)
        text_path = Path(handle.name)
    try:
        subprocess.run([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
            "-TextFile", str(text_path), "-OutputFile", str(output), "-Rate", str(rate),
        ], check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("Windows PowerShell is required for the local speech preview") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Windows Speech failed: {exc.stderr.strip()}") from exc
    finally:
        text_path.unlink(missing_ok=True)


def timestamp(seconds: float) -> str:
    minutes = int(seconds // 60)
    remaining = seconds - minutes * 60
    return f"{minutes:02d}:{remaining:05.2f}"


def render(spec: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [(section["name"], line) for section in spec["sections"] for line in section["lines"]]
    duration = float(spec["duration_seconds"])
    bpm = int(spec["bpm"])
    beat = 60.0 / bpm
    intro = beat * 8
    outro = beat * 8
    usable = max(duration - intro - outro, len(lines) * 3.5)
    line_slot = usable / max(len(lines), 1)
    actual_duration = intro + line_slot * len(lines) + outro
    backing = synth_backing(actual_duration, bpm, str(spec["key"]))
    lrc_lines = [f"[ti:{spec['title']}]", "[ar:Vocabulary Song local preview]"]
    timings: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="vocab-song-") as temp_name:
        temp_dir = Path(temp_name)
        for index, (section, line) in enumerate(lines):
            start = intro + index * line_slot
            voice_file = temp_dir / f"line-{index:03d}.wav"
            speak(line, voice_file, rate=1)
            clip, source_rate = read_wav_mono(voice_file)
            clip = resample(clip, source_rate)
            mix(backing, clip, start + 0.25, 0.88)
            lrc_lines.append(f"[{timestamp(start)}]{line}")
            timings.append({"section": section, "line": line, "start_seconds": round(start, 3)})

        pronunciation_parts: list[array.array] = []
        silence = array.array("h", [0]) * int(SAMPLE_RATE * 0.65)
        for index, word in enumerate(spec["words"]):
            phrase = f"{word['word']}. {word['word']}. {word['example']}"
            word_file = temp_dir / f"word-{index:03d}.wav"
            speak(phrase, word_file, rate=-1)
            clip, source_rate = read_wav_mono(word_file)
            pronunciation_parts.extend((resample(clip, source_rate), silence))

    pronunciation = array.array("h")
    for part in pronunciation_parts:
        pronunciation.extend(part)

    write_wav(out_dir / "preview.wav", backing)
    write_wav(out_dir / "pronunciation.wav", pronunciation)
    (out_dir / "lyrics.lrc").write_text("\n".join(lrc_lines) + "\n", encoding="utf-8")
    report = {
        "backend": "local-preview",
        "natural_singing": False,
        "sample_rate": SAMPLE_RATE,
        "duration_seconds": round(actual_duration, 3),
        "voice_engine": "Windows System.Speech",
        "timings": timings,
    }
    (out_dir / "render-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    spec = load_spec(args.spec.resolve())
    errors, warnings = validate(spec)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    render(spec, args.out.resolve())
    print(f"Created local preview in {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
