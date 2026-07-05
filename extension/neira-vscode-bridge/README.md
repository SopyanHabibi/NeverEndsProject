# Neira Bridge

**Neira Bridge** is a lightweight VS Code extension that connects your editor directly to [Neira](https://github.com/), a personal, local-first AI assistant running on Ollama.

This extension does **not** contain any AI logic, model, memory, or database of its own. It is purely a bridge: it collects context from your editor (selected code, active file, diagnostics) and forwards it to the Neira backend running on `localhost:5000`. All reasoning, memory, and conversation history are handled entirely by Neira itself.

## ⚠️ Requirement

**This extension only works if you have Neira installed and running locally.** It is not a standalone AI tool — it will not function without the Neira backend (`neira.py`) active on your machine.

This is a personal project built specifically to pair with Neira, and is not intended for general public use.

## How It Works

1. Select a block of code in the editor.
2. Right-click and choose **"Neira: Ask about this code"**.
3. The extension collects:
   - The selected code
   - The active file name
   - The current workspace/project name
   - Any diagnostics (errors/warnings) overlapping the selection
4. This context is sent to Neira's backend.
5. Your Neira browser tab automatically switches to a new "Project" session, shows a popup asking what you'd like to know, and streams the answer live once you submit.

## Why It's Built This Way

Neira is designed as a self-contained personal AI ecosystem. This extension deliberately avoids duplicating any AI functionality inside VS Code — it exists only to make it easier to hand code context over to Neira, wherever Neira happens to be running.

## Status

Actively evolving alongside the main Neira project. No fixed roadmap — features are added as needed.

---

Built by Ian, for Ian's own AI assistant, Neira. 🛠️
