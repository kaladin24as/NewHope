from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import generator, validator

app = FastAPI(title="Data Engineering Platform Generator")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "DataEng Generator"}

# Include routers (commented out until created)
app.include_router(generator.router, prefix="/api/v1/generator", tags=["generator"])
app.include_router(validator.router, prefix="/api/v1/validator", tags=["validator"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
