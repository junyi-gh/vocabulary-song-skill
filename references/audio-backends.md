# Audio backends

## Diagnostic preview backend

`scripts/build_lite_song.py` uses only Python's standard library plus Windows Speech and synthesizes a simple backing track. It creates:

- `preview.wav`: rhythmic English rehearsal over music;
- `pronunciation.wav`: target words and example sentences spoken normally;
- `lyrics.lrc`: timed lyric lines;
- `render-report.json`: backend and timing details.

This mode is fast and useful for internal checks of words, timing, and teaching design. It is not a natural singing model and is never an acceptable user-facing song delivery.

## ACE-Step full-song backend

The integration targets the official `ace-step/ACE-Step-1.5` project and pins release `v0.1.8`. ACE-Step is MIT-licensed and can generate complete songs with vocals and instruments.

The installer clones ACE-Step into a selected runtime directory and installs its environment with `uv`. The runtime location is stored locally in `.runtime-location`, which is excluded from Git. Source dependencies and model weights are too large for a Skill repository. Models are downloaded by ACE-Step on first use.

Run on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_acestep.ps1 -InstallRoot <large-drive-directory>
powershell -ExecutionPolicy Bypass -File scripts/start_acestep.ps1
```

The API defaults to `http://127.0.0.1:8001`. Then run:

```powershell
py -3 scripts/acestep_client.py --spec <song.json> --out <output-directory>
```

The client submits the verified lyrics, polls the asynchronous task, and downloads the returned audio. Set `ACESTEP_API_KEY` only if the server was started with authentication.

### Hardware note

ACE-Step supports CPU and Intel paths, but integrated graphics can be very slow and may require substantial RAM. On machines without a suitable GPU, test the local preview first. The Skill must not promise an ACE-Step completion time.

## ACE Music Cloud

Use `https://acemusic.ai/playground/create` when the user is signed in and local generation is impractical. Select **Cloud**, the highest-quality available ACE-Step model, and **Custom** mode. Map the song specification as follows:

- put `sections` into **Lyrics**, preserving section labels;
- put `style_prompt`, `arrangement`, and the complete `vocal` profile into **Prompt**;
- set duration, BPM, and time signature from the specification;
- leave key on Auto only when the UI does not accept the requested key, while retaining the key in the prompt;
- keep Thinking enabled for the first artistic render unless speed is more important;
- generate variants privately in **My Library** and never click **Publish** without an explicit user request.

After generation, play the track to verify that the vocal is sung and intelligible. Download the accepted private-library result when the interface supports it. Record the model and selected vocal profile beside the local song specification.

## Backend decision

1. Use diagnostic preview only for internal timing and pronunciation validation.
2. Use ACE-Step for every user-facing song acceptance test.
3. If local ACE-Step is impractical, use the official hosted Space through `scripts/acestep_space_client.py`. It requires `gradio_client`; an optional `HF_TOKEN` can be supplied for authenticated Hugging Face access.
4. If the hosted Space cannot allocate a GPU, use ACE Music Cloud after the user signs in.
5. A separately hosted ACE-Step server can instead be selected with `scripts/acestep_client.py --server <url>`.
