# SciOly Study Coach

A study site for Science Olympiad. Pick an event to:

- browse every practice test for it on Scioly.org (Test Exchange and wiki archive), newest first
- add downloaded tests (PDF, .docx or text) to a personal question bank
- drill quizzes from your bank or from AI-written questions
- ask an AI tutor about the event

The AI (Qwen2.5-1.5B via [WebLLM](https://github.com/mlc-ai/web-llm)) runs entirely in the visitor's browser on their own GPU. Nothing is sent to a server. It needs a recent Chrome or Edge with WebGPU and downloads about 1 GB on first use. Question banks and scores are stored in the visitor's browser.

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
