from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all routers
from .routers import auth, programs, documents, search, ai_assistance, emails
from .database import engine
from . import models

# Create database tables (consider using Alembic for migrations in production)
# Uncommenting to create missing tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Program Pal Pathfinder API",
    description="API for managing university program applications, documents, and insights.",
    version="0.1.1", # Increment version
)

# CORS Middleware
# Adjust origins as needed for your frontend
origins = [
    "http://localhost:5173", # Default Vite dev server port
    "http://localhost:3000", # Common React dev port
    "https://mxinchzj.manus.space", # Deployed frontend URL
    "*" # Allow all for now, restrict in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(programs.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(ai_assistance.router)
app.include_router(emails.router) # Include the new emails router

@app.get("/")
def read_root():
    return {"message": "Welcome to the Program Pal Pathfinder API"}


