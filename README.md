# Apex Legal AI

Apex Legal AI is a multi-agent decision support system designed to help legal professionals and safety teams investigate online harassment campaigns. It organizes raw comment feeds, analyzes threat categories, structures evidentiary timelines, groups coordinated campaigns, and compiles draft case reports for legal evaluation.

---

## Technical Stack

- **Multi-Agent Orchestration**: Google ADK
- **Reasoning Model**: Gemini
- **File System Sandbox**: Model Context Protocol (MCP) Server
- **Frontend App Interface**: Streamlit
- **Data Validation & Typing**: Pydantic v2

---

## Directory Structure

```
apex-legal-ai/
├── .agents/          # Workspace rules & behavior guidelines (AGENTS.md)
├── config/           # YAML/JSON configs for ADK and MCP
├── mcp/              # Local MCP server & secure file access logic
├── src/              # Application source code
│   ├── core/         # State definitions & Orchestrator workflow pipeline
│   ├── agents/       # Multi-agent definitions (Security, Evidence, Analysis, Campaign, Report)
│   ├── skills/       # Specific computational functions (sanitization, clustering)
│   └── frontend/     # Streamlit app interface & sub-views
├── tests/            # pytest suites
├── .env.example      # Environment variable template
├── requirements.txt  # Pinned dependencies list
└── pyproject.toml    # Python project package configuration
```

---

## Installation & Setup

1. **Clone the repository and enter the directory:**
   ```bash
   cd apex-legal-ai
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   - Copy `.env.example` to `.env`
   - Fill in your `GEMINI_API_KEY` and update configuration paths.

5. **Start the MCP Server:**
   ```bash
   python -m mcp.server
   ```

6. **Run the Streamlit frontend application:**
   ```bash
   streamlit run src/frontend/app.py
   ```

---

## Usage Workflow

1. **Ingest raw data**: Upload your CSV file containing abusive comments on the *Overview & Upload* page.
2. **Execute Agentic Pipeline**: The system automatically runs inputs through the ADK multi-agent pipeline (Security -> Evidence -> Analysis -> Campaign -> Report).
3. **Inspect Dashboard**: View identified semantic groups, temporal timelines, and threat categories.
4. **Approve & Export Case**: Human analyst reviews the auto-drafted markdown case file, edits sections as needed, and serializes the approved report via the local MCP server.
