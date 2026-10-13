from fastapi import FastAPI

app = FastAPI(
    title="PaisaLog API",
    version="0.1.0",
    description="Personal finance tracker backend.",
)


@app.get("/api/v1/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
