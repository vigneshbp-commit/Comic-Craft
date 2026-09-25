# 💥 ComicCraft - AI Comic Story Creator using Gemini Models

**ComicCraft** is an end-to-end Generative AI web application that automatically creates personalized 5-panel comic book stories, complete with panel titles, atmospheric scene descriptions, character dialogues, action narration, comic box captions, stylized illustrations, and an exportable, printable multi-page PDF book.

Powered by:
- **FastAPI**: Asynchronous high-performance Python web backend.
- **Google Gemini Flash (`gemini-1.5-flash`)**: Fast, structured 5-panel storyboard outline generation.
- **Google Gemini Pro (`gemini-1.5-pro`)**: Deep storytelling, character dialogues, and dynamic captions.
- **Stable Diffusion & Comic Canvas Engine**: Visual scene rendering with multi-tier fallback (Diffusers / Hugging Face Inference API / Pillow Procedural Halftone Comic Engine).
- **FPDF2**: Multi-page comic book compilation with cover page, panel graphics, captions, and narrative layout.
- **Jinja2 & Retro Comic CSS**: Immersive comic book visual identity with halftone textures, bold comic ink borders, and speech bubbles.

---

## 🏗️ Architecture & Component Overview

```
Comic-Craft _ Vicks/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application factory and static mounting
│   ├── config.py            # Environment and directory path management
│   ├── routes.py            # Route handlers (Form, JSON API, PDF download, test routes)
│   ├── gemini_flash.py      # Panel outline generation via Gemini Flash
│   ├── gemini_pro.py        # Dialogue, narration, and caption scripting via Gemini Pro
│   ├── image_generator.py   # Multi-tier comic illustration synthesis (SD / HF / Pillow)
│   ├── layout_builder.py    # Unifies outlines, stories, and illustrations into 5 panels
│   ├── exporters.py         # Multi-page comic book PDF exporter using FPDF2
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic schemas (PromptRequest, ComicResponse, etc.)
│   ├── static/
│   │   ├── css/style.css    # Custom retro comic-book stylesheet
│   │   ├── panels/          # Saved panel PNG illustrations
│   │   └── exports/         # Saved comic PDF documents
│   └── templates/
│       ├── base.html        # Common header, footer, comic fonts
│       ├── index.html       # Creation form with preset chips and loading indicator
│       ├── comic_preview.html # 5-panel sequential comic viewer & PDF download action
│       └── export_success.html # Download confirmation and new comic CTA
├── tests/
│   ├── __init__.py
│   ├── test_services.py     # Unit tests for AI & export modules
│   └── test_routes.py       # Integration tests for FastAPI endpoints
├── .vscode/
│   ├── launch.json          # Pre-configured VS Code debug & run profiles
│   └── settings.json        # Python interpreter & pytest configuration
├── .env.example             # Template for API keys and configuration
├── .env                     # Local environment settings
├── requirements.txt         # Project dependencies
├── run.py                   # One-click launcher script
└── README.md                # Comprehensive documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Git

### 2. Environment Setup

```bash
# 1. Clone repository and navigate into project directory
cd "Comic-Craft _ Vicks"

# 2. Create Python virtual environment
python3 -m venv comiccraft-env

# 3. Activate the virtual environment
# On Linux / macOS:
source comiccraft-env/bin/activate
# On Windows (cmd/PowerShell):
comiccraft-env\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
```

### 3. API Keys Configuration
Create or update your `.env` file in the project root:

```bash
cp .env.example .env
```

Open `.env` and fill in your API key:
```env
# Get your free Gemini API key from: https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key_here

# (Optional) Hugging Face token for Stable Diffusion cloud inference
HF_API_KEY=your_hf_token_here

# Image Generation Backend: auto (recommended), procedural, hf_api, local
IMAGE_GEN_BACKEND=auto
```

> **Note on Zero-Configuration Mode**: If no `GEMINI_API_KEY` is provided, ComicCraft automatically engages its built-in creative story and comic synthesis engine, allowing you to test, develop, and preview the full pipeline immediately without any missing API key crashes!

---

## 💻 Running the Application

### Option A: Using the Launcher Script
```bash
python run.py
```

### Option B: Using Uvicorn Directly
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once started, open your browser and navigate to:
- **Web Application**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🎨 VS Code Setup & Debugging

This project includes ready-to-use VS Code configurations in `.vscode/`:
1. Open the project folder in **Visual Studio Code**.
2. When prompted to select a Python Interpreter, choose `./comiccraft-env/bin/python`.
3. Press **F5** or go to the **Run & Debug** tab:
   - Select **"FastAPI: Run ComicCraft Server"** to start the app with auto-reloading and breakpoint debugging.
   - Select **"Pytest: Run All Tests"** to debug automated test suites directly in VS Code.

---

## 🧪 Testing the Application

### 1. Run Automated Test Suite
To execute all unit and integration tests:

```bash
pytest tests/ -v
```

All tests verify outline generation, script creation, image rendering, layout assembly, PDF file generation, and HTTP endpoint responses.

---

### 2. REST API Testing via cURL

#### Generate Comic via JSON API:
```bash
curl -X POST "http://127.0.0.1:8000/generate-comic/json" \
  -H "Content-Type: application/json" \
  -d '{
    "story_prompt": "A courageous fox exploring an enchanted forest to find a fallen star",
    "character_name": "Rusty",
    "setting": "Enchanted Forest",
    "tone": "Dramatic",
    "art_style": "Comic Book"
  }'
```

#### Test Image Generator Endpoint:
```bash
curl -X POST "http://127.0.0.1:8000/test-image" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Rusty the fox discovering a glowing starry crystal in deep woodland",
    "panel_number": 1,
    "art_style": "Comic Book"
  }'
```

#### Health Diagnostic Endpoint:
```bash
curl http://127.0.0.1:8000/health
```

---

## 📖 Application Walkthrough & User Stories

### Scenario 1: Creating a Dramatic Epic
1. Open `http://127.0.0.1:8000`.
2. Click the **"🦊 Brave Fox"** preset chip or type your own prompt:
   - Prompt: *"A brave fox exploring an enchanted forest to find the sacred spring"*
   - Protagonist: *Rusty*
   - Setting: *Enchanted Forest*
   - Tone: *Dramatic & Epic*
   - Art Style: *Classic Comic Book*
3. Click **"GENERATE MY 5-PANEL COMIC!"**.
4. The loading indicator tracks generation across all stages.
5. In the Comic Preview, inspect all 5 sequential panels:
   - Panel Titles & Numbers
   - Comic Illustrations
   - Scene Descriptions in italics
   - Yellow Comic Caption Boxes
   - Character Dialogue Speech Bubbles
   - Action Narration
6. Click **"Download Your Comic as PDF"**:
   - The multi-page PDF automatically downloads to your device.
   - You are redirected to the Export Success page with options to re-download or create another comic.

### Scenario 2: Lighthearted & Funny Cartoon Iteration
1. On the homepage, select or type:
   - Prompt: *"A clumsy robot trying to bake a birthday cake in a futuristic kitchen"*
   - Protagonist: *Bolts*
   - Setting: *Futuristic Cyber City*
   - Tone: *Funny & Lighthearted*
   - Art Style: *Anime / Manga Graphic Novel*
2. Submit to regenerate the comic strip with humorous narration and matching visuals.

---

## 🛠️ Technical Details & Resilient Fallbacks

- **Multi-Tier Image Synthesis**:
  - **Tier 1 (Local Diffusers)**: Loads `runwayml/stable-diffusion-v1-5` when a compatible GPU and packages are available.
  - **Tier 2 (HF Inference API)**: Calls Hugging Face Serverless API when `HF_API_KEY` is configured.
  - **Tier 3 (Comic Canvas Engine)**: High-resolution procedural comic illustration generator built using Pillow. Crafts vibrant gradient palettes, halftone comic textures, action sunbursts, bold borders, panel tags, and scene banners. Guaranteed zero downtime, no GPU requirements, and instant execution.
- **Smart Character Encoding in PDF**:
  - Automatically cleans smart quotes, curly dashes, and non-Latin symbols to ensure PDF export never crashes.

---

## 📜 License
ComicCraft is open-source under the MIT License.
