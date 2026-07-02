# Apex Legal AI: AI Workspace Behavior Rules

## General Principles
1. **Decision Support Only:** The AI agents must never assume legal authority. Never draft content that claims "This is a violation of law section X." Instead, write "Exhibits characteristics of doxxing / threat of violence as defined by the safety policies."
2. **Neutral tone:** All communications, summary write-ups, and logs should remain highly professional, objective, and detached.
3. **No direct file writes:** All file edits/creation relating to case data, exported reports, or system audit logs must use the MCP server interfaces (`mcp:write_case_report`, etc.) to guarantee sandbox safety and audit trail logging.

## Safety & Inputs
- **Prompt Injection Defense:** Always sanitize input structures before passing to down-stream classification models.
- **PII Scrubbing:** Strip personal emails, personal phone numbers, and physical addresses from analyzed comment datasets unless they correspond explicitly to target entities designated by the user in the case session config.
