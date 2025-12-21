"""
App name: Quantum Computing Simulation
Description: FastAPI application entry point. Defines all API routes for CRUD operations
             on quantum computing entities (States, Gates, Simulations, Shots).
"""

import os
from pathlib import Path
from datetime import date
from fastapi import FastAPI, Request, Form, Response, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from usecase.index_usecase import IndexUsecase
from usecase.gates_usecase import GatesUsecase
from usecase.states_usecase import StatesUsecase
from usecase.shots_usecases import ShotsUsecase
from usecase.simulations_usecase import SimulationsUsecase
from utils.constants import Constants
import tempfile

code = Constants.ResponseCode

# ----- Paths / env -----
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)
FRONTEND_DIR = BASE_DIR / "frontend"

# ----- Database (Neon PostgreSQL) -----
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    pool_recycle=280,
    connect_args={"connect_timeout": 10},
)

# ----- Rate Limiting -----
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Static & templates
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(FRONTEND_DIR / "template"))


# ============================================
#  Daily Budget Guards
# ============================================
DAILY_QUERY_LIMIT = 500  # Max simulations per day
DAILY_RESET_LIMIT = 10   # Max resets per day


def get_daily_count(name: str) -> int:
    """Get daily counter value from temp file."""
    filename = os.path.join(tempfile.gettempdir(), f"{name}_{date.today()}.count")
    try:
        with open(filename) as f:
            return int(f.read())
    except FileNotFoundError:
        return 0


def increment_count(name: str):
    """Increment daily counter."""
    filename = os.path.join(tempfile.gettempdir(), f"{name}_{date.today()}.count")
    count = get_daily_count(name) + 1
    with open(filename, "w") as f:
        f.write(str(count))


# ============================================
#  Helper Functions
# ============================================
def _build_response(response: dict):
    """
    Convert usecase response dict to appropriate FastAPI response.
    Handles 204 No Content (empty body) vs JSON responses.
    """
    if response["status_code"] == code.CODE_204:
        return Response(status_code=code.CODE_204)
    return JSONResponse(
        content=response["context"],
        status_code=response["status_code"]
    )


# ============================================
#  Health Checks
# ============================================
@app.get("/health")
def health():
    """Health check endpoint."""
    return {"ok": True}


@app.get("/db-ping")
@limiter.limit("30/minute")
def db_ping(request: Request):
    """Database connectivity check."""
    try:
        with engine.connect() as conn:
            db = conn.execute(text("SELECT current_database()")).scalar()
        return JSONResponse({"ok": True, "database": db})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ============================================
#  Top page
# ============================================
@app.get("/", response_class=HTMLResponse)
@limiter.limit("60/minute")
def index(request: Request):
    """Render the homepage."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Quantum Simulator"},
    )


@app.post("/reset")
@limiter.limit("5/minute")
def reset_db(request: Request):
    """Reset database to initial state with sample data."""
    # Daily budget guard
    if get_daily_count("resets") >= DAILY_RESET_LIMIT:
        raise HTTPException(503, "Daily reset limit reached. Try tomorrow.")
    
    response = IndexUsecase(engine).reset()
    
    if response["status_code"] == code.CODE_200:
        increment_count("resets")
    
    return _build_response(response)


# ============================================
#  States
# ============================================
@app.get("/states", response_class=HTMLResponse)
@limiter.limit("60/minute")
def get_states(request: Request):
    """Retrieve and display all quantum states."""
    response = StatesUsecase(engine).show()
    return templates.TemplateResponse(
        "states.html",
        status_code=response["status_code"],
        context={"request": request, **response.get("context", {})}
    )


@app.post("/states")
@limiter.limit("20/minute")
def post_states(
    request: Request,
    stateName: str = Form(...),
    stateSymbol: str = Form(...),
    alphaReal: float = Form(...),
    alphaImgn: float = Form(...),
    betaReal: float = Form(...),
    betaImgn: float = Form(...),
    description: str = Form(...)
):
    """Add a new quantum state."""
    data = {
        "name": stateName,
        "symbol": stateSymbol,
        "alphaReal": alphaReal,
        "alphaImgn": alphaImgn,
        "betaReal": betaReal,
        "betaImgn": betaImgn,
        "description": description
    }
    response = StatesUsecase(engine).add(data)
    return _build_response(response)


@app.put("/states/{state_id}")
@limiter.limit("20/minute")
def put_states(
    request: Request,
    state_id: int,
    stateName: str = Form(...),
    stateSymbol: str = Form(...),
    alphaReal: float = Form(...),
    alphaImgn: float = Form(...),
    betaReal: float = Form(...),
    betaImgn: float = Form(...),
    description: str = Form(...)
):
    """Update an existing quantum state."""
    data = {
        "stateID": state_id,
        "name": stateName,
        "symbol": stateSymbol,
        "alphaReal": alphaReal,
        "alphaImgn": alphaImgn,
        "betaReal": betaReal,
        "betaImgn": betaImgn,
        "description": description
    }
    response = StatesUsecase(engine).edit(data)
    return _build_response(response)


@app.delete("/states/{state_id}")
@limiter.limit("20/minute")
def delete_states(request: Request, state_id: int):
    """Delete a quantum state by ID."""
    response = StatesUsecase(engine).delete(state_id)
    return _build_response(response)


# ============================================
#  Gates (read-only)
# ============================================
@app.get("/gates", response_class=HTMLResponse)
@limiter.limit("60/minute")
def get_gates(request: Request):
    """Retrieve and display all quantum gates."""
    response = GatesUsecase(engine).show()
    return templates.TemplateResponse(
        "gates.html",
        status_code=response["status_code"],
        context={"request": request, **response.get("context", {})}
    )


# ============================================
#  Simulations
# ============================================
@app.get("/simulations", response_class=HTMLResponse)
@limiter.limit("60/minute")
def get_simulations(request: Request):
    """Retrieve and display all simulations."""
    response = SimulationsUsecase(engine).show()
    return templates.TemplateResponse(
        "simulations.html",
        status_code=response["status_code"],
        context={"request": request, **response.get("context", {})}
    )


@app.post("/simulations")
@limiter.limit("10/minute")
async def post_simulations(request: Request, background_tasks: BackgroundTasks):
    """
    Create a new simulation with shots.
    Returns 202 Accepted immediately, shots are generated in background.
    Client should poll /simulations/{simID}/progress for status.
    """
    # Daily budget guard
    if get_daily_count("simulations") >= DAILY_QUERY_LIMIT:
        raise HTTPException(503, "Daily simulation limit reached. Try tomorrow.")
    
    data = await request.json()
    usecase = SimulationsUsecase(engine)
    
    # Start simulation (returns immediately with simID)
    response = usecase.add_async(data)
    
    # If simulation was created successfully, start background shot generation
    if response["status_code"] == code.CODE_202:
        sim_id = response["context"]["simID"]
        background_tasks.add_task(
            usecase.generate_shots_background,
            sim_id,
            data
        )
        increment_count("simulations")
    
    return _build_response(response)


@app.get("/simulations/{sim_id}/progress")
@limiter.limit("120/minute")
def get_simulation_progress(request: Request, sim_id: int):
    """
    Get progress of shot generation for a simulation.
    Returns current/total shots and status (processing/complete/error).
    """
    progress = SimulationsUsecase.get_progress(sim_id)
    
    if progress is None:
        return JSONResponse(
            content={"message": f"Progress not found for simulation ID {sim_id}"},
            status_code=code.CODE_404
        )
    
    return JSONResponse(content=progress, status_code=code.CODE_200)


@app.delete("/simulations/{sim_id}/progress")
@limiter.limit("60/minute")
def clear_simulation_progress(request: Request, sim_id: int):
    """
    Clear progress tracking for a simulation (cleanup after complete).
    """
    SimulationsUsecase.clear_progress(sim_id)
    return Response(status_code=code.CODE_204)


@app.delete("/simulations/{sim_id}")
@limiter.limit("20/minute")
def delete_simulation(request: Request, sim_id: int):
    """Delete a simulation and its associated shots."""
    response = SimulationsUsecase(engine).delete(sim_id)
    return _build_response(response)


# ============================================
#  Shots
# ============================================
@app.get("/shots", response_class=HTMLResponse)
@limiter.limit("60/minute")
def get_shots(request: Request):
    """Retrieve and display all measurement shots."""
    response = ShotsUsecase(engine).show()
    return templates.TemplateResponse(
        "shots.html",
        status_code=response["status_code"],
        context={"request": request, **response.get("context", {})}
    )


@app.get("/shots/{sim_id}", response_class=HTMLResponse)
@limiter.limit("60/minute")
def filter_shots(request: Request, sim_id: int):
    """Filter and display shots by simulation ID."""
    response = ShotsUsecase(engine).filter(sim_id)
    return templates.TemplateResponse(
        "shots.html",
        status_code=response["status_code"],
        context={"request": request, **response.get("context", {})}
    )


# ============================================
#  Tutorial
# ============================================
@app.get("/tutorial", response_class=HTMLResponse)
@limiter.limit("60/minute")
def get_tutorial(request: Request):
    """Return the tutorial page."""
    return templates.TemplateResponse(
        "tutorial.html",
        {"request": request, "title": "Quantum Simulator"},
    )
