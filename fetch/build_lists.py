#!/usr/bin/env python3
"""Build aria2 input files for the bulk download (library, maps, models).

Writes lists/{library,maps,models}.txt (aria2 --input-file format) plus
lists/summary.txt. Container paths: /library = $LIBRARY_DIR,
/models = $MODELS_DIR (see stack/bulk.compose.yaml). Stdlib only.
"""
import base64
import gzip
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "lists"
UA = {"User-Agent": "offline-library-fetch"}
HAVE = {"wikivoyage_en_all", "zimgit-water_en", "survivorlibrary.com_en_all"}  # already on the NAS


def get(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def gb(n):
    return f"{n / 1e9:.1f} GB"


def library():
    lines, total = [], 0
    for z in json.loads((ROOT.parent / "content" / "zims.json").read_text()):
        if z["name"] in HAVE:
            continue
        lines += [z["torrent"], "  dir=/library/incoming", "  follow-torrent=mem", "  seed-time=0"]
        total += z["size_bytes"]
    return lines, total, []


def maps():
    lines, notes = [], []
    b = json.loads(get("https://build-metadata.protomaps.dev/builds.json"))[-1]
    md5 = base64.b64decode(b["md5sum"]).hex()
    lines += [f"https://build.protomaps.com/{b['key']}", "  dir=/library/incoming",
              "  out=planet.pmtiles", f"  checksum=md5={md5}", "  split=16",
              "  max-connection-per-server=16"]
    total = b["size"]
    raw = get("https://download.osmand.net/get_indexes?gzip=true", 120)
    idx = ET.fromstring(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw)
    n = 0
    for r in idx.iter("region"):
        if r.get("type") != "map":
            continue
        name = r.get("name")
        lines += [f"https://download.osmand.net/download?standard=yes&file={name}",
                  "  dir=/library/phone-maps/osmand", f"  out={name}"]
        total += int(r.get("containerSize") or 0)
        n += 1
    notes.append(f"Protomaps {b['key']} {gb(b['size'])}; OsmAnd {n} world map files")
    return lines, total, notes


# (folder, exact HF repo, file regex). Pinned owners only: no search, so a look-alike upload can't slip in.
MODELS = [
    ("qwen/Qwen3.8-27B", "unsloth/Qwen3.8-27B-GGUF", r"UD-Q6_K_XL|mmproj-F16"),
    ("gemma/gemma-4-31B-it", "unsloth/gemma-4-31B-it-GGUF", r"UD-Q6_K_XL|mmproj-F16"),
    ("qwen/Qwen3.6-35B-A3B", "unsloth/Qwen3.6-35B-A3B-GGUF", r"UD-Q6_K[^_]|UD-Q6_K\.|mmproj-F16"),
    ("gemma/gemma-4-26B-A4B-it", "unsloth/gemma-4-26B-A4B-it-GGUF", r"Q4_K_M|mmproj-F16"),
    ("nvidia/Nemotron-3.5-Bolt-74B-A9B", "unsloth/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-GGUF", r"UD-Q4_K_XL"),
    ("nvidia/Nemotron-3.5-Super-VL-120B-A12B", "unsloth/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-GGUF", r"UD-Q4_K_XL|mmproj-F16"),
    ("qwen/Qwen3.8-Flash-Next", "unsloth/Qwen3.8-Flash-Next-GGUF", r"UD-Q4_K_XL"),
    ("deepseek/DeepSeek-V4.1-Flash-1017", "unsloth/DeepSeek-V4.1-Flash-1017-GGUF", r"UD-Q4_K_XL"),
    ("gemma/gemma-4-12B-it", "unsloth/gemma-4-12B-it-GGUF", r"Q4_K_M|mmproj-F16"),
    ("gemma/gemma-4-E4B-it", "unsloth/gemma-4-E4B-it-GGUF", r"Q4_K_M|mmproj-F16"),
    # MLX copies of the phone models, for MLX phone apps such as Locally AI (GGUF above stays for PocketPal/llama.cpp).
    ("phone-mlx/gemma-4-E4B-it-qat-mobile", "mlx-community/gemma-4-E4B-it-qat-mobile", r"."),
    ("phone-mlx/medgemma-1.5-4b-it-4bit", "mlx-community/medgemma-1.5-4b-it-4bit", r"."),
    ("medical/medgemma-27b-it", "unsloth/medgemma-27b-text-it-GGUF", r"Q4_K_M|mmproj-F16"),
    ("medical/medgemma-1.5-4b-it", "unsloth/medgemma-1.5-4b-it-GGUF", r"Q8_0|mmproj-F16"),
    ("embeddings/Qwen3-Embedding-8B", "Qwen/Qwen3-Embedding-8B-GGUF", r"Q8_0"),
    ("embeddings/Qwen3-Embedding-0.6B", "Qwen/Qwen3-Embedding-0.6B-GGUF", r"Q8_0"),
    ("embeddings/Qwen3-Reranker-4B", "mradermacher/Qwen3-Reranker-4B-GGUF", r"Q8_0"),
    ("ocr/GLM-OCR", "zai-org/GLM-OCR", r"."),
    ("ocr/Unlimited-OCR-2", "baidu/Unlimited-OCR-2", r"."),
    ("speech/Nemotron-3.5-Transcribe-30B-A4B", "AtomicChat/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B-GGUF",
     r"AD-IQ4_NL\.gguf$|Encoder-F16\.gguf$"),
    ("speech/whisper.cpp", "ggerganov/whisper.cpp", r"ggml-large-v3(-turbo)?\.bin$"),
    ("speech/parakeet-tdt-0.6b-v3", "nvidia/parakeet-tdt-0.6b-v3", r"."),
    ("speech/Kokoro-82M", "hexgrad/Kokoro-82M", r"."),
    ("translation/translategemma-12b", "mradermacher/translategemma-12b-it-GGUF", r"Q4_K_M"),
    ("image/Z-Image-Turbo", "Tongyi-MAI/Z-Image-Turbo", r"."),
]
SIDECARS = r"(^|/)(README\.md|LICENSE[^/]*|.*\.jinja|config\.json|tokenizer[^/]*|generation_config\.json)$"


def models():
    lines, total, notes = [], 0, []
    for folder, repo, pattern in MODELS:
        try:
            tree = json.loads(get(f"https://huggingface.co/api/models/{repo}/tree/main?recursive=1"))
        except urllib.error.HTTPError as e:
            notes.append(f"FAILED {folder} {repo}: HTTP {e.code}")
            continue
        picked = [f for f in tree if f["type"] == "file"
                  and (re.search(pattern, f["path"]) or re.search(SIDECARS, f["path"]))]
        weights = [f for f in picked if f.get("lfs")]
        if not weights:
            notes.append(f"NO MATCH {folder} {repo} /{pattern}/")
            continue
        size = sum(f.get("lfs", {}).get("size") or f.get("size", 0) for f in picked)
        total += size
        notes.append(f"{folder:45} {repo}  {gb(size)}")
        for f in picked:
            sub = str(Path(f["path"]).parent)
            dest = f"/models/models/{folder}" + ("" if sub == "." else f"/{sub}")
            lines += [f"https://huggingface.co/{repo}/resolve/main/{f['path']}", f"  dir={dest}",
                      f"  out={Path(f['path']).name}"]
            if f.get("lfs", {}).get("oid"):
                lines.append(f"  checksum=sha-256={f['lfs']['oid']}")
    return lines, total, notes


def main():
    OUT.mkdir(exist_ok=True)
    summary = []
    for name, fn in (("library", library), ("maps", maps), ("models", models)):
        lines, total, notes = fn()
        (OUT / f"{name}.txt").write_text("\n".join(lines) + "\n")
        summary += [f"== {name}: {gb(total)}"] + notes
    (OUT / "summary.txt").write_text("\n".join(summary) + "\n")
    print("\n".join(summary))


if __name__ == "__main__":
    sys.exit(main())
