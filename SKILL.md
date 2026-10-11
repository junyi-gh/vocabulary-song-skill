---
name: vocabulary-song
description: Turn supplied or randomly selected English vocabulary into a short learning song, pronunciation drill, lyric sheet, and playable audio. Use when a learner wants to memorize words through music, practise English word stress, or generate an ACE-Step song from a vocabulary list; do not use for ordinary songwriting without a learning goal.
---

# Vocabulary Song

Create a compact song whose first priority is accurate, memorable vocabulary learning and whose second priority is musical polish.

## Choose the mode

- **Learning package**: produce the verified word cards, lyrics, song prompt, and exercises. Use when the user does not request audio.
- **Diagnostic preview**: `scripts/build_lite_song.py` may be used internally to check timing and pronunciation tracks. It is speech over music, not a song, and must not be presented as the requested musical result.
- **Full song**: use the local ACE-Step adapter in `scripts/acestep_client.py` when a suitable server is available, `scripts/acestep_space_client.py` for the official hosted Space, or ACE Music Cloud when the user is signed in and local hardware is impractical. Read [references/audio-backends.md](references/audio-backends.md) before installing, starting, or calling a backend.

When the user requests playable music, the acceptance artifact must contain sung lyrics with a musical vocal performance. Do not substitute text-to-speech, a spoken chant, or an instrumental track.

## Gather or infer the inputs

Accept a user list or select words when the user requests random vocabulary. Default to:

- 4–6 target words from one approximate level;
- General American pronunciation;
- 60–90 seconds, pop/folk/hip-hop according to word rhythm;
- a positive, concrete micro-story rather than unrelated lines.

Ask only when a missing choice would materially change the result. Otherwise state the defaults briefly and proceed. If the user supplies a personal word-list file, sample from it rather than inventing words.

## Choose musical style, instrumentation, and voice

If the user does not specify a style, offer or infer up to three suitable directions and explain the learning tradeoff briefly. Examples include pop, acoustic folk, rock, R&B/soul, jazz, electronic, hip-hop, and cinematic. Read [references/style-presets.md](references/style-presets.md) when building the generation prompt.

Treat a style as an arrangement decision, not a decorative label. Define:

- tempo, meter, harmonic mood, groove, and section-level energy arc;
- at least three audible instrumental roles: rhythm, harmony, and melodic or textural color;
- a vocal format such as female lead, male lead, duet, close harmony, or choir;
- vocal register and timbre, accent, diction, emotional delivery, and dynamic development.

If the user does not choose a voice, select one that supports both the subject and clear English learning, and state the choice before generation. Do not imitate a named living singer. A requested vocal profile is a target characteristic, not a guarantee of an identical fixed voice across model generations.

## Handle fully random word sets

Before drafting, classify the set by semantic cohesion:

- **Coherent**: the words naturally share a scene or theme. Write one continuous story song.
- **Bridgeable**: the words differ but can take distinct narrative roles such as setting, object, action, conflict, and resolution. Use one unifying metaphor and make the bridge explain the connection.
- **Distant**: the words would require strained meanings or unnatural grammar. Use a clearly framed concept such as memories in a suitcase, pages in a notebook, or scenes in a dream. If depth would still suffer, split the set into a short song series and tell the user why.

Offer two priorities when they genuinely conflict:

- **Strict coverage** keeps every supplied word in one song and may sound more playful or episodic.
- **Artistic depth** keeps the strongest 4–6 words in the main song and moves semantic outliers into a companion song or reprise.

Default to one song for up to 6 random words. For 7–10 highly unrelated words, prefer two linked songs; above 10, split into a mini-album. Never silently omit a supplied word.

## Verify the vocabulary before writing

For every target word, establish:

- canonical spelling and intended sense;
- part of speech and concise Chinese meaning;
- IPA for the chosen accent, syllable split, and primary stress;
- one natural collocation and one learner-level example.

For rare, disputed, or unfamiliar entries, consult an authoritative dictionary when internet access is available. Flag homographs whose pronunciation changes with meaning. Never invent an IPA transcription to make a rhyme work.

Read [references/learning-design.md](references/learning-design.md) when choosing repetitions, fitting stress to beats, or checking educational quality.

## Write for memory and pronunciation

1. Build one coherent situation that makes the meanings inferable.
2. Place each target word in at least two meaningful contexts; use 2–4 audible repetitions total.
3. Put the stressed syllable on a strong beat. Do not split a target word across notes, alter its stress, or use an unnatural grammar solely for rhyme.
4. Put the clearest target-word repetitions in the chorus or hook.
5. Keep lines short enough to articulate. Prefer near-rhyme or no rhyme over distorted pronunciation.
6. Include a spoken pronunciation pre-roll or separate pronunciation track; a sung token is not a pronunciation authority.

## Create the song package

Prepare a UTF-8 JSON file matching `assets/example-song.json`. Required top-level fields are:

- `title`, `style_prompt`, `bpm`, `key`, `duration_seconds`;
- `arrangement`, containing at least three named `instruments` plus a section-level `arc`;
- `vocal`, containing `format`, `timbre`, `accent`, `diction`, and `delivery`;
- `words`, each with `word`, `ipa`, `stress`, `meaning_zh`, `part_of_speech`, `collocation`, and `example`;
- `sections`, each with `name` and `lines`.

Keep section names compatible with music generators, such as `Verse 1`, `Chorus`, `Bridge`, and `Outro`. Do not place IPA or Chinese translations in sung lyrics.

Also provide a concise Markdown learning sheet containing:

1. the word cards;
2. lyrics with target words visually emphasized;
3. a pronunciation drill;
4. three retrieval exercises: meaning recall, lyric gap-fill, and learner-created sentence;
5. a suggested review schedule: immediately, next day, three days, and seven days.

## Render audio

For an internal diagnostic preview only:

```powershell
py -3 scripts/build_lite_song.py --spec <song.json> --out <output-directory>
```

For a full ACE-Step song, first make sure the local API is running, then use:

```powershell
py -3 scripts/acestep_client.py --spec <song.json> --out <output-directory>
```

When local hardware is impractical, use the official hosted Space:

```powershell
py -3 scripts/acestep_space_client.py --spec <song.json> --out <output-directory>
```

If the hosted Space has no GPU allocation and the user is signed in to ACE Music Cloud, follow the Custom-mode mapping in [references/audio-backends.md](references/audio-backends.md). Keep the result private unless the user explicitly asks to publish it.

Render into a task output directory, not inside the skill folder. Preserve the JSON and learning sheet beside the audio so a generation can be reproduced.

## Present the finished song

Never present a playable song as an audio player or download link alone. In the same response or demo page:

- show the song title, style, vocal profile, and target words;
- place the complete section-labelled lyrics directly beside or immediately below the audio;
- visually emphasize every target word in the displayed lyrics;
- link the learning sheet and song specification only as optional supporting material.

The learner must be able to listen and follow the words without opening another file. If the interface cannot display synchronized lyrics, use a clearly readable static lyric block rather than hiding the lyrics behind a link.

## Quality gate

Before presenting the result:

- run `scripts/validate_spec.py <song.json>`;
- confirm every target word appears in the lyrics at least twice;
- show a coverage summary mapping every word to its lyric contexts;
- confirm that each repetition teaches the selected sense rather than merely naming the word;
- listen to or inspect the generated audio when possible;
- confirm that the lyric is audibly sung rather than spoken and that the vocal has melody, phrasing, and an intentional timbre;
- confirm that the chosen vocal format and timbre are perceptible and that the words remain intelligible;
- confirm that the arrangement contains real musical roles—rhythm, harmony, and melodic or textural color—rather than a bare loop;
- confirm that the delivered audio and complete visible lyrics appear together in the user-facing result;
- reject instrumental-only output, inaudible vocals, robotic text-to-speech, or a track whose lyrics are unrelated to the supplied words;
- assess musical beauty separately from vocabulary coverage: arrangement, vocal tone, emotional arc, hook, and intelligibility must all be acceptable;
- report which backend was used;
- never claim that a synthetic singing voice is the sole correct pronunciation model.

If audio generation fails, return the complete learning package and the exact next action needed; do not silently substitute unrelated audio.
