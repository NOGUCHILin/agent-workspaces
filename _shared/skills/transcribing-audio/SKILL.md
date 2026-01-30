---
name: transcribing-audio
description: Use this skill when transcribing audio or video files to text, creating SRT subtitles, or converting speech to text. Triggers on keywords like "transcribe", "subtitles", "speech-to-text", "audio to text", "video transcription", "SRT", "captions".
---

# Audio Transcription Skill

Transcribe audio/video files using faster-whisper (large-v3-turbo model).

## Quick Start

```bash
# SRT subtitle (default)
~/dev/whisper-transcribe/.venv/bin/whisper-transcribe "input.mp4"

# JSON with timestamps
~/dev/whisper-transcribe/.venv/bin/whisper-transcribe "input.mp4" output.json --format json

# Plain text
~/dev/whisper-transcribe/.venv/bin/whisper-transcribe "input.mp4" output.txt --format txt
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--format` | srt | Output format: srt, json, txt |
| `--lang` | ja | Language code (ja, en, etc.) |

## Output Formats

### SRT (default)
```srt
1
00:00:00,000 --> 00:00:05,200
こんにちは

2
00:00:05,200 --> 00:00:10,400
今日は良い天気ですね
```

### JSON
```json
{
  "language": "ja",
  "segments": [{"start": 0.0, "end": 5.2, "text": "こんにちは"}],
  "words": [{"start": 0.0, "end": 0.5, "word": "こんにちは", "probability": 0.95}]
}
```

## Examples

```bash
# Transcribe single file
~/dev/whisper-transcribe/.venv/bin/whisper-transcribe "/path/to/video.mp4"

# Batch transcribe (bash loop)
for f in *.m4a; do
  ~/dev/whisper-transcribe/.venv/bin/whisper-transcribe "$f"
done

# English audio
~/dev/whisper-transcribe/.venv/bin/whisper-transcribe "english.mp4" --lang en
```

## Specs

- **Model**: large-v3-turbo (fixed)
- **Memory**: ~6GB
- **Speed**: 8-12 min per 10 min audio
- **Accuracy**: High
