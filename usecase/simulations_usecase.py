"""
App name: Quantum Computing Simulation
Description: Usecase class for managing CRUD operations on the Simulations entity,
             including quantum gate calculations, shot generation, and progress tracking.
"""

from usecase.base_usecase import UsecaseBase
from usecase.quantum_core_usecase import generate_shots, generate_shots_random_noise, is_supported_gate
from utils.constants import Constants
from utils.logger import logger
from utils.decorators import db_error_handler

from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause
import threading

table = Constants.Tables
col = Constants.Columns
sp = Constants.StoredProcedures
code = Constants.ResponseCode


class SimulationsUsecase(UsecaseBase):
    """
    A usecase class responsible for managing the operations performed 
    on the application's Quantum Simulations page.
    """

    # Class-level progress store shared across instances
    # Format: {simID: {"current": int, "total": int, "status": str, "message": str}}
    _progress_store: dict = {}
    _progress_lock = threading.Lock()

    def __init__(self, engine):
        super().__init__(engine)
    
    # ==========================================
    # Progress Tracking Methods
    # ==========================================
    
    @classmethod
    def _init_progress(cls, sim_id: int, total: int, state_symbol: str, gate_symbol: str):
        """Initialize progress tracking for a simulation."""
        with cls._progress_lock:
            cls._progress_store[sim_id] = {
                "current": 0,
                "total": total,
                "status": "processing",
                "message": f"Applying {gate_symbol} to {state_symbol}",
                "state_symbol": state_symbol,
                "gate_symbol": gate_symbol
            }
        logger.debug(f"Progress initialized for simID {sim_id}: 0/{total}")

    @classmethod
    def _update_progress(cls, sim_id: int, current: int):
        """Update progress for a simulation."""
        with cls._progress_lock:
            if sim_id in cls._progress_store:
                cls._progress_store[sim_id]["current"] = current
        logger.debug(f"Progress updated for simID {sim_id}: {current}")

    @classmethod
    def _complete_progress(cls, sim_id: int):
        """Mark simulation as complete."""
        with cls._progress_lock:
            if sim_id in cls._progress_store:
                cls._progress_store[sim_id]["status"] = "complete"
                cls._progress_store[sim_id]["current"] = cls._progress_store[sim_id]["total"]
                cls._progress_store[sim_id]["message"] = "Complete"
        logger.debug(f"Progress completed for simID {sim_id}")

    @classmethod
    def _error_progress(cls, sim_id: int, error_msg: str):
        """Mark simulation as errored."""
        with cls._progress_lock:
            if sim_id in cls._progress_store:
                cls._progress_store[sim_id]["status"] = "error"
                cls._progress_store[sim_id]["message"] = error_msg
        logger.error(f"Progress error for simID {sim_id}: {error_msg}")

    @classmethod
    def get_progress(cls, sim_id: int) -> dict | None:
        """
        Get progress for a simulation.
        Returns None if simID not found in progress store.
        """
        with cls._progress_lock:
            if sim_id not in cls._progress_store:
                return None
            
            progress = cls._progress_store[sim_id].copy()
            total = progress["total"]
            current = progress["current"]
            pct = int((current / total) * 100) if total > 0 else 0
            
            return {
                "simID": sim_id,
                "current": current,
                "total": total,
                "pct": pct,
                "status": progress["status"],
                "message": progress["message"],
                "state_symbol": progress.get("state_symbol", ""),
                "gate_symbol": progress.get("gate_symbol", "")
            }

    @classmethod
    def clear_progress(cls, sim_id: int):
        """Remove progress tracking for a simulation (cleanup)."""
        with cls._progress_lock:
            if sim_id in cls._progress_store:
                del cls._progress_store[sim_id]
        logger.debug(f"Progress cleared for simID {sim_id}")

    # ==========================================
    # Validation Methods
    # ==========================================
    
    def _validate_simulation_data(self, data: dict) -> tuple[bool, str, dict]:
        """
        Validate simulation parameters.
        Args:
            data: Dictionary containing stateID, gateID, numShots
        Returns: (is_valid, error_message, recommended_values)
        """
        try:
            # State ID validation
            state_id = data.get("stateID")
            if not state_id:
                return False, "Initial state is required", {}
            
            try:
                int(state_id)
            except (ValueError, TypeError):
                return False, "State ID must be a valid number", {}
            
            # Gate ID validation
            gate_id = data.get("gateID")
            if not gate_id:
                return False, "Gate is required", {}
            
            try:
                int(gate_id)
            except (ValueError, TypeError):
                return False, "Gate ID must be a valid number", {}
            
            # Number of shots validation
            num_shots = data.get("numShots")
            if num_shots is None:
                return False, "Number of shots is required", {}
            
            try:
                num_shots = int(num_shots)
            except (ValueError, TypeError):
                return False, "Number of shots must be a valid number", {}
            
            if num_shots < 5 or num_shots > 100:
                return False, "Number of shots must be between 5 and 100", {}
            
            return True, "", {}
            
        except (ValueError, TypeError) as e:
            return False, f"Invalid data format: {str(e)}", {}

    def _get_gate_symbol_by_id(self, gate_id: int) -> str | None:
        """
        Look up gate symbol from the Gates table by gate ID.
        Returns: Gate symbol if found, None otherwise
        """
        sql = text(f'SELECT "symbol" FROM "{table.GATES}" WHERE "gateID" = :gate_id')
        result = self._execute(sql, {"gate_id": gate_id})
        row = result.mappings().fetchone()
        return row["symbol"] if row else None

    def _get_state_symbol_by_id(self, state_id: int) -> str | None:
        """
        Look up state symbol from the States table by state ID.
        Returns: State symbol if found, None otherwise
        """
        sql = text(f'SELECT "symbol" FROM "{table.STATES}" WHERE "stateID" = :state_id')
        result = self._execute(sql, {"state_id": state_id})
        row = result.mappings().fetchone()
        return row["symbol"] if row else None

    def _strip_symbol_wrapper(self, symbol: str) -> str:
        """
        Strip the || wrapper from gate symbol.
        Example: |X| -> X
        """
        if symbol and symbol.startswith('|') and symbol.endswith('|'):
            return symbol[1:-1]
        return symbol

    # ==========================================
    # CRUD Methods
    # ==========================================

    @db_error_handler
    def show(self):
        """Retrieve all Simulation entity records from the Database."""
        logger.info("START SimulationsUsecase.show")

        # Simulation table with joined data
        sql = self._build_simulation_query()
        result = self._execute(sql)
        sim_data = [dict(row) for row in result.mappings().all()]
        logger.debug(f"sim_data:{sim_data}")

        # States dropdown
        sql = self._build_state_symbol_dropdown()
        result = self._execute(sql)
        state_data = [dict(row) for row in result.mappings().all()]
        logger.debug(f"state_data:{state_data}")

        # Gates dropdown
        sql = self._build_gate_symbol_dropdown()
        result = self._execute(sql)
        gate_data = [dict(row) for row in result.mappings().all()]
        logger.debug(f"gate_data:{gate_data}")

        data = {
            "sim_data": sim_data,
            "state_data": state_data,
            "gate_data": gate_data
        }

        logger.info("END SimulationsUsecase.show")
        return self._build_json_response(code.CODE_200, "OK", data)

    @db_error_handler
    def add_async(self, data: dict):
        """
        Start a new Simulation (returns immediately with simID).
        Shots are generated in background via generate_shots_background().
        
        Returns 202 Accepted with simID for progress polling.
        """
        logger.info("START SimulationsUsecase.add_async")
        logger.debug(f"Request Body:{data}")

        # Validate input
        is_valid, error_msg, recommended_values = self._validate_simulation_data(data)
        if not is_valid:
            logger.warning(f"Validation failed: {error_msg}")
            return self._build_json_response(
                code.CODE_400, 
                error_msg, 
                recommended_values if recommended_values else None
            )

        state_id = int(data.get("stateID"))
        gate_id = int(data.get("gateID"))
        num_shots = int(data.get("numShots"))

        # Look up gate symbol
        gate_symbol_wrapped = self._get_gate_symbol_by_id(gate_id)
        if gate_symbol_wrapped is None:
            logger.warning(f"Gate not found in database: ID={gate_id}")
            return self._build_json_response(
                code.CODE_404, 
                f"Gate with ID {gate_id} not found in database.", 
                None
            )

        # Look up state symbol
        state_symbol = self._get_state_symbol_by_id(state_id)
        if state_symbol is None:
            logger.warning(f"State not found in database: ID={state_id}")
            return self._build_json_response(
                code.CODE_404, 
                f"State with ID {state_id} not found in database.", 
                None
            )

        # Insert simulation record
        sp_param = {"p_stateID": state_id, "p_gateID": gate_id}
        sql = self._build_sp_call(sp.SP_INSERT_SIMULATION, sp_param)
        logger.debug(f"SQL:{sql}")
        
        result = self._execute(sql, sp_param)
        row = result.mappings().fetchone()
        
        if row[col.CODE] != 201:
            return self._build_json_response(row[col.CODE], row[col.MSG], None)
        
        sim_id = row["simID"]
        logger.debug(f"Created simulation with ID: {sim_id}")

        # Initialize progress tracking
        self._init_progress(sim_id, num_shots, state_symbol, gate_symbol_wrapped)

        logger.info("END SimulationsUsecase.add_async")
        
        # Return 202 Accepted with simID for polling
        return {
            "status_code": code.CODE_202,
            "context": {
                "message": "Simulation started",
                "simID": sim_id,
                "total": num_shots
            }
        }

    def generate_shots_background(self, sim_id: int, data: dict):
        """
        Generate shots in background (called by FastAPI BackgroundTasks).
        Updates progress after each shot.
        """
        logger.info(f"START generate_shots_background for simID {sim_id}")
        
        try:
            state_id = int(data.get("stateID"))
            gate_id = int(data.get("gateID"))
            num_shots = int(data.get("numShots"))

            # Look up gate symbol
            gate_symbol_wrapped = self._get_gate_symbol_by_id(gate_id)
            gate_symbol = self._strip_symbol_wrapper(gate_symbol_wrapped)
            logger.debug(f"Gate symbol: {gate_symbol_wrapped} -> {gate_symbol}")

            # Get initial state data
            state_sql = text(f"""
                SELECT "alphaReal", "alphaImgn", "betaReal", "betaImgn" 
                FROM "{table.STATES}" 
                WHERE "stateID" = :state_id
            """)
            result = self._execute(state_sql, {"state_id": state_id})
            state_row = result.mappings().fetchone()
            
            if not state_row:
                self._error_progress(sim_id, "State not found")
                return

            # Get initial state amplitudes
            alpha_real = float(state_row["alphaReal"])
            alpha_imgn = float(state_row["alphaImgn"])
            beta_real = float(state_row["betaReal"])
            beta_imgn = float(state_row["betaImgn"])

            # Generate shots based on gate type
            if is_supported_gate(gate_symbol):
                logger.info(f"Using quantum gate logic for standard gate: {gate_symbol}")
                shots_data = generate_shots(
                    alpha_real=alpha_real,
                    alpha_imgn=alpha_imgn,
                    beta_real=beta_real,
                    beta_imgn=beta_imgn,
                    gate_symbol=gate_symbol,
                    num_shots=num_shots
                )
            else:
                logger.info(f"Using random noise logic for custom gate: {gate_symbol}")
                shots_data = generate_shots_random_noise(
                    alpha_real=alpha_real,
                    alpha_imgn=alpha_imgn,
                    beta_real=beta_real,
                    beta_imgn=beta_imgn,
                    num_shots=num_shots
                )

            # Insert shots one by one, updating progress after each
            for i, shot in enumerate(shots_data):
                shot_param = {
                    "p_simid": sim_id,
                    "p_alphareal": float(shot["alphaReal"]),
                    "p_alphaimgn": float(shot["alphaImgn"]),
                    "p_betareal": float(shot["betaReal"]),
                    "p_betaimgn": float(shot["betaImgn"]),
                    "p_outputstate": shot["outputState"]
                }
                shot_sql = self._build_sp_call(sp.SP_INSERT_SHOT, shot_param)
                self._execute(shot_sql, shot_param)
                
                # Update progress after each shot
                self._update_progress(sim_id, i + 1)

            # Mark as complete
            self._complete_progress(sim_id)
            logger.info(f"END generate_shots_background for simID {sim_id}")

        except Exception as e:
            logger.error(f"Error in generate_shots_background: {e}", exc_info=True)
            self._error_progress(sim_id, f"Error generating shots: {str(e)}")

    @db_error_handler
    def delete(self, sim_id: int):
        """Delete a Simulation entity record. Shots are deleted via CASCADE."""
        logger.info("START SimulationsUsecase.delete")

        sp_param = {"p_simID": sim_id}
        sql = self._build_sp_call(sp.SP_DELETE_SIMULATION, sp_param)
        logger.debug(f"SQL:{sql}")
        
        result = self._execute(sql, sp_param)
        row = result.mappings().fetchone()

        logger.info("END SimulationsUsecase.delete")
        return self._build_json_response(row[col.CODE], row[col.MSG], None)

    def _build_simulation_query(self) -> TextClause:
        """Build query to get simulations with state, gate, and shot count."""
        sql = f"""
            SELECT
                "{table.SIMULATIONS}"."simID" AS "simID",
                "{table.STATES}"."symbol" AS "initialState",
                "{table.GATES}"."symbol" AS "gateSymbol",
                COUNT("{table.SHOTS}"."shotID") AS "numOfShots"
            FROM "{table.SIMULATIONS}"
            INNER JOIN "{table.STATES}" ON "{table.SIMULATIONS}"."stateID" = "{table.STATES}"."stateID"
            INNER JOIN "{table.GATES}" ON "{table.SIMULATIONS}"."gateID" = "{table.GATES}"."gateID"
            LEFT JOIN "{table.SHOTS}" ON "{table.SIMULATIONS}"."simID" = "{table.SHOTS}"."simID"
            GROUP BY "{table.SIMULATIONS}"."simID", "{table.STATES}"."symbol", "{table.GATES}"."symbol"
            ORDER BY "{table.SIMULATIONS}"."simID" ASC;
        """
        return text(sql)
