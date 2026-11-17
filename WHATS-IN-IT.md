# What's in the offline library

A self-hosted, works-with-no-internet library on a home NAS: encyclopedias, how-to and survival
references, world maps for phones, and a shelf of open AI models. Everything is free/open content,
downloaded once and checksum-verified. **Total: about 1.75 TB.**

| Category | Size |
|---|---|
| Reference & learning library | 499 GB |
| Maps | 256 GB |
| AI models | 989 GB |

Software: [Kiwix](https://kiwix.org) serves the library (offline, full-text search),
[Protomaps](https://protomaps.com) + MapLibre for the browser map, [OsmAnd](https://osmand.net)
on phones, [Open WebUI](https://openwebui.com) + llama.cpp for AI chat on a local machine, and
an MLX app such as Locally AI for AI on phones.

## 1. Library (Kiwix ZIM files)

| Section | What's in it | Size |
|---|---|---|
| **Reference** | Wikipedia (English, full with images), Simple English Wikipedia, Wiktionary, Wikibooks, Wikisource, Wikiversity, Wikivoyage, ArchWiki | 157 GB |
| **Preparedness** | Survivor Library (thousands of old how-to books as PDFs: farming, tools, medicine, crafts), US Army field manuals, Ready.gov, True Prepper, Post Disaster Resource Library, Outdoors Q&A, knots | 233 GB |
| **Learning** | CrashCourse videos, LibreTexts textbooks (biology, chemistry, physics, math, engineering, medicine, K-12…), Project Gutenberg (science, technology, agriculture, medicine, geography…), Stack Exchange Q&A for math/physics/biology/chemistry | 92 GB |
| **Repair & build** | iFixit repair guides, Appropedia, CD3WD (development/appropriate-tech archive), motor vehicle mechanics, Q&A for electronics, home improvement, engineering, woodworking | 12 GB |
| **Medical** | WikiMed and MDWiki medical encyclopedias, a medical library, military medicine, Medical Sciences Q&A | 4 GB |
| **Water & food** | Water treatment library, Food for Preppers, cooking and gardening Q&A | 1 GB |
| **Power & energy** | Low-Tech Magazine (solar-powered edition), amateur radio Q&A | 1 GB |

## 2. Maps

| What | Use | Size |
|---|---|---|
| Protomaps planet (whole world, street level) | Browser map with GPS "you are here" | 140 GB |
| OsmAnd map files, every country / US state (1,050 files) | Turn-by-turn navigation on phones with no signal; copy just the regions you need | 117 GB |

## 3. AI models

Open-weight models, mostly GGUF (llama.cpp) 4–6-bit quantizations. "Needs" is the rough
memory class: GPU VRAM + system RAM on a PC (MoE models can offload experts to RAM), or
unified memory on Apple silicon.

**General chat & reasoning**

| Model | Size | Needs |
|---|---|---|
| Qwen 3.8 27B | 26 GB | 64 GB unified memory |
| Gemma 4 31B (vision) | 29 GB | 64 GB unified memory |
| Qwen 3.6 35B-A3B (fast MoE) | 30 GB | 48 GB (GPU + RAM) |
| Gemma 4 26B-A4B (fast MoE, vision) | 18 GB | 32 GB+ |
| Nemotron 3.5 Bolt 74B-A9B | 50 GB | 64 GB unified memory |
| Gemma 4 12B | 7 GB | 16 GB+ |
| Nemotron 3.5 Super VL 120B-A12B | 87 GB | 128 GB (archive for now) |
| Qwen 3.8 Flash-Next 125B-A6B | 111 GB | 128 GB (archive for now) |
| DeepSeek V4.1 Flash | 512 GB+ (archive only) |

**Phone-sized**

| Model | Size | Notes |
|---|---|---|
| Gemma 4 E4B (GGUF + MLX "QAT mobile") | 6 + 3.5 GB | Everyday on-phone assistant |
| MedGemma 1.5 4B (GGUF + MLX 4-bit) | 5 + 3.4 GB | Medical questions on the phone |

**Specialists**

| Job | Models | Size |
|---|---|---|
| Medical | MedGemma 27B | 17 GB |
| Search over the library (embeddings + reranker) | Qwen3 Embedding 8B and 0.6B, Qwen3 Reranker 4B | 13 GB |
| Reading scanned pages (OCR) | GLM-OCR, Unlimited-OCR-2 | 10 GB |
| Speech to text | Nemotron 3.5 Transcribe, Whisper large-v3 (+turbo), Parakeet TDT v3 | 32 GB |
| Text to speech | Kokoro 82M | 0.4 GB |
| Translation | TranslateGemma 12B | 7 GB |
| Image generation | Z-Image Turbo | 33 GB |

## Keeping it current

A monthly job checks for newer Wikipedia/ZIM builds, map builds, and new model releases and posts
a summary; updates are pulled by hand. Wikipedia itself refreshes every few months.

*Medical content is for reference when no professional is reachable, not a substitute for one.*
