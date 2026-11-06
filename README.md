# SciOly Study Coach

A study site for Science Olympiad. Pick an event to:

- browse every practice test for it on Scioly.org (Test Exchange and wiki archive), newest first
- add downloaded tests (PDF, .docx or text) to a personal question bank
- drill quizzes from your bank or from AI-written questions
- ask an AI tutor about the event

The AI runs entirely in the visitor's browser on their own GPU via [WebLLM](https://github.com/mlc-ai/web-llm): Qwen2.5-1.5B (about 1 GB download) or Qwen2.5-3B (about 2 GB, needs 8 GB+ RAM). Nothing is sent to a server. It needs a recent Chrome or Edge with WebGPU. Question banks and scores are stored in the visitor's browser.

If you run [OmniRoute](https://github.com/diegosouzapw/OmniRoute) on your own computer, pick "OmniRoute on this computer" in the AI model menu to use your own providers instead (`http://localhost:20128/v1`, model `auto`). Add at least one provider in the OmniRoute dashboard first. The API key box is optional for a local OmniRoute.

## Test catalog

`docs/catalog.json` holds links and metadata only. The tests belong to their writers and stay hosted on Scioly.org. To refresh it:

```bash
python3 tools/build_catalog.py
```

The script follows scioly.org's robots.txt (3-second crawl delay, no `/wiki/index.php` pages).

## Hosting

GitHub Pages serves the `docs/` folder. To run locally:

```bash
python3 -m http.server 8000 --directory docs
```
