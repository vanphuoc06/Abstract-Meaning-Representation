import os
import sys
import time
import penman
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

# Add root path and metric directory to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
for p in [PROJECT_ROOT, os.path.join(PROJECT_ROOT, "ssharp", "metric")]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from rose.scorer_hash import RoSE


app = FastAPI(
    title="SEMCAT / RoSE - AMR Evaluation API",
    description="Backend API for Semantic Evaluation Metric Conforming to AMR Theory (SEMCAT / RoSE)",
    version="1.0.0"
)

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Preset Example AMR Pairs
EXAMPLES = [
    {
        "id": "exact_match",
        "title": "1. Exact Match (Trùng khớp 100%)",
        "description": "Hai đồ thị AMR giống hệt nhau cả về khái niệm (concepts) và vai trò ngữ nghĩa (roles).",
        "ref": "(c / chase-01\n   :ARG0 (d / dog)\n   :ARG1 (ct / cat))",
        "hyp": "(c / chase-01\n   :ARG0 (d / dog)\n   :ARG1 (ct / cat))",
        "n_iter": 3,
        "tau": 0.99
    },
    {
        "id": "swapped_roles",
        "title": "2. Swapped Roles (Tráo đổi vai trò ngữ nghĩa)",
        "description": "Cùng khái niệm chó & mèo, nhưng tráo đổi vai trò chủ thể ARG0 và đối thể ARG1 ('Con chó đuổi con mèo' vs 'Con mèo đuổi con chó').",
        "ref": "(c / chase-01\n   :ARG0 (d / dog)\n   :ARG1 (ct / cat))",
        "hyp": "(c / chase-01\n   :ARG0 (ct / cat)\n   :ARG1 (d / dog))",
        "n_iter": 3,
        "tau": 0.99
    },
    {
        "id": "structural_reified",
        "title": "3. Reified / Passive Form (Đồng nghĩa cấu trúc)",
        "description": "Biểu diễn câu chủ động vs bị động hoặc đảo góc nhìn node chính (:ARG0-of), tuy cấu trúc bề mặt khác nhưng cùng ý nghĩa logic.",
        "ref": "(c / chase-01\n   :ARG0 (d / dog)\n   :ARG1 (ct / cat))",
        "hyp": "(d / dog\n   :ARG0-of (c / chase-01\n      :ARG1 (ct / cat)))",
        "n_iter": 3,
        "tau": 0.99
    },
    {
        "id": "low_similarity",
        "title": "4. Low Similarity (Khác biệt ý nghĩa)",
        "description": "Hai câu mang ngữ nghĩa hoàn toàn khác nhau.",
        "ref": "(b / bark-01\n   :ARG0 (d / dog\n      :mod (b2 / big)))",
        "hyp": "(r / read-01\n   :ARG0 (g / girl)\n   :ARG1 (b / book))",
        "n_iter": 3,
        "tau": 0.99
    }
]

class EvaluateRequest(BaseModel):
    ref_amr: str = Field(..., description="Reference AMR string in PENMAN notation")
    hyp_amr: str = Field(..., description="Hypothesis AMR string in PENMAN notation")
    num_iterations: int = Field(3, ge=2, le=10, description="Weisfeiler-Leman iterations N")
    similarity_threshold_tau: float = Field(0.99, ge=0.5, le=0.99, description="Similarity threshold tau")

class BatchItem(BaseModel):
    id: Optional[str] = None
    ref_amr: str
    hyp_amr: str

class BatchEvaluateRequest(BaseModel):
    items: List[BatchItem]
    num_iterations: int = Field(3, ge=2, le=10)
    similarity_threshold_tau: float = Field(0.99, ge=0.5, le=0.99)

def parse_graph_stats(amr_str: str):
    """Parse PENMAN AMR string and extract visual graph metrics"""
    g = penman.loads(amr_str)[0] if isinstance(penman.loads(amr_str), list) else penman.loads(amr_str)
    instances = g.instances()
    edges = g.edges()
    attributes = g.attributes()
    
    return {
        "top_concept": g.top,
        "variables_count": len(instances),
        "edges_count": len(edges),
        "attributes_count": len(attributes),
        "total_triples": len(g.triples),
        "concepts": [f"{i.source} / {i.target}" for i in instances],
        "roles": list(set([e.role for e in edges]))
    }

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "SEMCAT / RoSE AMR API", "timestamp": time.time()}

@app.get("/api/examples")
def get_examples():
    return {"examples": EXAMPLES}

@app.post("/api/evaluate")
def evaluate_amr(req: EvaluateRequest):
    start_time = time.time()
    
    if not req.ref_amr.strip() or not req.hyp_amr.strip():
        raise HTTPException(status_code=400, detail="Reference AMR và Hypothesis AMR không được để trống!")
        
    # Syntax check Reference
    try:
        ref_graph = penman.loads(req.ref_amr)
    except Exception as e:
        return JSONResponse(status_code=422, content={
            "success": False,
            "error_type": "SyntaxError",
            "target": "Reference AMR",
            "message": f"Lỗi cú pháp trong Reference AMR: {str(e)}"
        })

    # Syntax check Hypothesis
    try:
        hyp_graph = penman.loads(req.hyp_amr)
    except Exception as e:
        return JSONResponse(status_code=422, content={
            "success": False,
            "error_type": "SyntaxError",
            "target": "Hypothesis AMR",
            "message": f"Lỗi cú pháp trong Hypothesis AMR: {str(e)}"
        })

    try:
        scorer = RoSE(
            num_iterations=int(req.num_iterations),
            similarity_threshold_tau=float(req.similarity_threshold_tau)
        )
        score_dict = scorer.compute_from_string(req.ref_amr, req.hyp_amr)
        metric_name = scorer.name()
        score_val = score_dict.get(metric_name, 0.0)
        
        # Calculate stats
        ref_stats = parse_graph_stats(req.ref_amr)
        hyp_stats = parse_graph_stats(req.hyp_amr)
        
        # Verdict classification
        if score_val >= 0.8:
            verdict_code = "HIGH"
            verdict_text = "Rất tương đồng / Đồng nghĩa (High Similarity)"
            color = "#10B981"
        elif score_val >= 0.4:
            verdict_code = "MODERATE"
            verdict_text = "Tương đồng một phần (Moderate Similarity)"
            color = "#F59E0B"
        else:
            verdict_code = "LOW"
            verdict_text = "Khác biệt ý nghĩa / Bất tương đồng (Low Similarity)"
            color = "#EF4444"

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        
        return {
            "success": True,
            "score": round(score_val, 4),
            "score_percentage": round(score_val * 100, 2),
            "metric_name": metric_name,
            "verdict": {
                "code": verdict_code,
                "text": verdict_text,
                "color": color
            },
            "parameters": {
                "num_iterations": req.num_iterations,
                "tau": req.similarity_threshold_tau
            },
            "stats": {
                "reference": ref_stats,
                "hypothesis": hyp_stats
            },
            "elapsed_ms": elapsed_ms
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tính toán RoSE: {str(e)}")

@app.post("/api/evaluate-batch")
def evaluate_batch(req: BatchEvaluateRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="Danh sách items rỗng!")

    scorer = RoSE(
        num_iterations=int(req.num_iterations),
        similarity_threshold_tau=float(req.similarity_threshold_tau)
    )
    
    results = []
    scores = []
    
    for i, item in enumerate(req.items):
        try:
            score_dict = scorer.compute_from_string(item.ref_amr, item.hyp_amr)
            score_val = score_dict.get(scorer.name(), 0.0)
            scores.append(score_val)
            results.append({
                "index": i + 1,
                "id": item.id or f"item_{i+1}",
                "score": round(score_val, 4),
                "status": "success"
            })
        except Exception as e:
            results.append({
                "index": i + 1,
                "id": item.id or f"item_{i+1}",
                "score": 0.0,
                "status": "error",
                "error": str(e)
            })
            
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0
    
    return {
        "success": True,
        "total_items": len(req.items),
        "average_score": avg_score,
        "metric_name": scorer.name(),
        "items": results
    }

# Serve Frontend static files
STATIC_DIR = os.path.join(CURRENT_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
