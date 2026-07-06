# Apex Legal AI Architecture

Apex Legal AI utilizes a multi-agent orchestration pattern built on top of the Google Agent Development Kit (ADK) and powered by Gemini.

The architecture is designed to cleanly separate concerns: ingesting raw data, organizing evidence, performing LLM-based safety evaluations, analyzing broader campaign patterns, and finally generating a human-in-the-loop legal review document.

## System Workflow

```mermaid
graph TD
    A([CSV Upload]) -->|Raw Data| B[Data Sanitization]
    B -->|Sanitized Comments| C[Evidence Agent]
    
    C -->|Structured Evidence| D[Gemini Classification Agent]
    D -->|Safety & Risk Labels| E[Campaign Detection Agent]
    
    E -->|Threat Clusters| F[Report Generator]
    F -->|Draft Markdown| G([Investigation Report])
    
    classDef input fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#01579b
    classDef process fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#e65100
    classDef agent fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#4a148c
    classDef output fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#1b5e20
    
    class A input
    class B process
    class C,D,E,F agent
    class G output
```

### Agent Roles

1. **Evidence Agent** (`EvidenceAgent`): Responsible for transforming raw unstructured input (such as rows from a CSV) into standardized `EvidenceRecord` schemas containing timestamps, platform information, and raw text.
2. **Analysis Agent** (`AnalysisAgent`): Interfaces with the Gemini LLM to semantically evaluate each piece of evidence. It assigns categories (Safe, Spam, Harassment, Threat) and severity scores based on carefully tuned system prompts.
3. **Campaign Agent** (`CampaignAgent`): Analyzes the output of the Analysis Agent across the entire dataset to detect coordinated inauthentic behavior, such as spam clusters or brigading attacks, by utilizing similarity clustering.
4. **Report Agent** (`ReportAgent`): Compiles all findings into a comprehensive Markdown report, rendering tables, calculating statistics, and adding the required human-in-the-loop review checklists.
