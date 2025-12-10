from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.health import router as health_router
from backend.routes.auth_routes import router as auth_router
from backend.routes.subsidy_routes import router as subsidy_router

app = FastAPI(title="Public Subsidy Transparency Ledger - API (v1)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(subsidy_router, prefix="/subsidies", tags=["Subsidies"])

@app.get("/")
async def root():
    return {"message": "Public Subsidy Transparency Ledger API - v1"}
