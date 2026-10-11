# Vocabulary Song Skill / 英语单词歌曲学习 Skill

Turn unfamiliar English words into a memorable song with sung vocals, a real instrumental arrangement, pronunciation guidance, and retrieval practice.

把陌生英文单词放进一首真正有人声演唱和多乐器伴奏的歌曲中，同时生成音标、重音、歌词学习单与复习练习。

> This is a learning workflow, not a text-to-speech track laid over background music. A user-facing result must contain melodic singing and an intentional arrangement.

## What it does / 功能

- Accepts supplied vocabulary or selects random words at a suitable level.
- Connects unrelated words through a story, metaphor, or short song series without silently omitting any word.
- Verifies spelling, meaning, IPA, stress, collocations, and learner-level examples.
- Lets the learner choose pop, folk, rock, R&B/soul, jazz, electronic, hip-hop, or cinematic styles.
- Supports female or male lead, duet, close harmony, choir, register, vocal timbre, accent, diction, and emotional delivery.
- Requires at least three musical roles across rhythm, harmony, and melodic or textural color.
- Produces a reproducible JSON song specification, lyric sheet, pronunciation drill, retrieval exercises, and full-song audio.
- Rejects instrumental-only results, buried vocals, robotic speech, unrelated lyrics, and bare backing loops.

## Public demo / 公开演示

**A Life Is Not a Price** teaches five words: `treatment`, `commercial`, `advertise`, `industry`, and `inflation`.

- Style: deep cinematic indie soul / R&B
- Voice: warm natural female alto with clear General American diction
- Instruments: piano, electric bass, live drums, clean electric guitar, cinematic strings, and restrained backing harmonies
- Backend: ACE Music Cloud, ACE-Step V1.5 XL Turbo
- Duration: 90 seconds
- Result: accepted by the learner as “很好听” after rejecting an earlier robotic speech-over-music prototype

[▶ Listen to the full public demo](examples/a-life-is-not-a-price/a-life-is-not-a-price.mp3)

### Lyrics / 歌词

#### Verse 1

Under the clinic light, she waits for **treatment**  
Her hands hold a bill she cannot understand  
Outside, a **commercial** promises salvation  
Bright smiling faces say relief is close at hand

#### Pre-Chorus

They **advertise** a miracle in thirty seconds  
But pain does not disappear when the slogan ends

#### Chorus

**Treatment** should be more than a number in a line  
When **inflation** climbs, a life is not a price  
**Industry**, remember every heartbeat has a name  
Keep the **commercial**, but don't sell hope away  
**Advertise** the truth: no one should stand alone  
**Treatment** is a promise we owe to every home

#### Verse 2

The **industry** grows taller over quiet streets  
**Inflation** turns tomorrow into borrowed time  
A **commercial** fades, but the waiting room remembers  
What they **advertise** can never measure life

#### Bridge

Let the **industry** build, but let compassion lead  
Let **inflation** fall before it buries every need  
If you **advertise** a cure, make care the first concern  
Let **treatment** reach the hands that wait their turn

#### Final Chorus

**Treatment** should be more than a number in a line  
When **inflation** climbs, a life is not a price  
**Industry**, remember every heartbeat has a name  
No **commercial** is worth more than the hope we save

- [Learning sheet and lyrics](examples/a-life-is-not-a-price/learning-sheet.md)
- [Reproducible song specification](examples/a-life-is-not-a-price/song.json)
- [Acceptance record](examples/a-life-is-not-a-price/acceptance-test.md)

## Install / 安装

Download or clone this repository as a folder named `vocabulary-song`, then place it in your Codex skills directory:

```text
~/.codex/skills/vocabulary-song/
```

Restart or refresh Codex so it can discover `SKILL.md`. The Skill is configured for automatic discovery and can also be invoked explicitly with `$vocabulary-song`.

For the optional official Hugging Face Space client:

```powershell
py -m pip install -r requirements.txt
```

Large ACE-Step model files are not included in this repository. The local installer downloads them only when local full-song generation is requested.

## Try it / 使用示例

```text
使用 $vocabulary-song 把 treatment、commercial、advertise、industry、inflation
做成一首 90 秒、女中音演唱的电影感 R&B 英文学习歌曲。
```

```text
Use $vocabulary-song to choose five random B1 English words and turn them into
an acoustic folk learning song with a warm male baritone and clear pronunciation.
```

If style or voice is omitted, the Skill chooses a suitable combination and states it before generation.

## Full-song backends / 完整歌曲生成方式

| Backend | Best for | Notes |
|---|---|---|
| ACE Music Cloud | Computers without a suitable GPU | Sign-in required; use Cloud + Custom mode. Keep results private unless the user asks to publish. |
| Official ACE-Step Space | Quick hosted experiments | Free GPU allocation can be unavailable or queued. Optional `HF_TOKEN` improves access priority. |
| Local ACE-Step 1.5 | Privacy and reproducibility | Models are downloaded separately and need substantial disk space; CPU-only generation can be very slow. |
| Diagnostic preview | Internal timing checks only | Uses speech over synthetic music and must never be presented as the finished song. |

See [audio backend details](references/audio-backends.md) for setup and routing.

## Output package / 输出内容

Each learning package contains:

1. verified vocabulary cards with IPA, stress, Chinese meaning, collocations, and examples;
2. lyrics that use every target word in meaningful contexts;
3. selectable style, instrumentation, arrangement arc, and vocal profile;
4. a pronunciation drill and spaced-retrieval exercises;
5. a validated JSON song specification;
6. full-song audio when a singing backend is available.

## Repository layout

```text
vocabulary-song/
├── SKILL.md
├── agents/openai.yaml
├── assets/example-song.json
├── examples/a-life-is-not-a-price/
├── references/
├── scripts/
├── requirements.txt
└── LICENSE
```

## Privacy and responsible use

- Personal vocabulary lists and generated songs stay local unless a cloud backend is deliberately used.
- Never publish a cloud-library song without the user's explicit approval.
- Do not request imitation of a named living singer.
- A synthetic singing voice is a memory aid, not the sole authority for pronunciation.
- Verify originality and permissions before commercial distribution.

## License

The Skill code and documentation are released under the MIT License. ACE-Step is an independent MIT-licensed project and is not bundled here. The public demo audio and lyrics are included with the user's permission for listening and evaluation; no separate reuse license is granted for the demo media.

