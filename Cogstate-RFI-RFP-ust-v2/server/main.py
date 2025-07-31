import uvicorn
from rfiprocessor.api.controller import app
from fastapi.middleware.cors import CORSMiddleware

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "rfiprocessor.api.controller:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 