from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import StringIO
import uuid
import pandas as pd
from io import StringIO

from src.core.state import InvestigationState, CommentData
from src.core.orchestrator import ApexLegalOrchestrator

app = FastAPI(
    title="Apex Legal AI",
    version="1.0"
)

# Allow React frontend to access the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Apex Legal AI Backend Running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/investigation")
async def start_investigation(
    case_name: str = Form(...),
    file: UploadFile = File(...)
):
    contents = await file.read()

    df = pd.read_csv(StringIO(contents.decode("utf-8")))

    comments = []

    for _, row in df.iterrows():
        comments.append(
            CommentData(
                comment_id=str(row["comment_id"]),
                platform=str(row["platform"]),
                username=str(row["username"]),
                timestamp=pd.to_datetime(row["timestamp"]),
                comment_text=str(row["comment_text"]),
            )
        )

    state = InvestigationState(
        case_id=str(uuid.uuid4()),
        case_name=case_name,
        raw_comments=comments,
    )

    orchestrator = ApexLegalOrchestrator()

    result = await orchestrator.execute_investigation(state)

    return {
        "case_id": result.state.case_id,
        "case_name": result.state.case_name,
        "pipeline_ok": result.pipeline_ok,
        "total_comments": len(result.state.raw_comments),
        "sanitized_comments": len(result.state.sanitized_comments),
        "campaigns_found": len(result.state.campaign_clusters),
        "report": result.state.report_draft_markdown,
    }