"""
App name: Quantum Computing Simulation
Description: Usecase class for managing CRUD operations on the Quantum States entity,
             including normalization validation for quantum state amplitudes.
"""

from usecase.base_usecase import UsecaseBase
from utils.constants import Constants
from utils.logger import logger
from utils.decorators import db_error_handler
import math

table = Constants.Tables
col = Constants.Columns
sp = Constants.StoredProcedures
code = Constants.ResponseCode


class StatesUsecase(UsecaseBase):
    """
    A usecase class responsible for managing the operations performed
    on the application's Quantum States page.
    """

    def __init__(self, engine):
        super().__init__(engine)

    def _validate_state_data(self, data: dict) -> tuple[bool, str, dict]:
        """
        Validate quantum state parameters.
        Args:
            data: Dictionary containing state data (name, symbol, amplitudes, description)
        Returns: (is_valid, error_message, recommended_values)
        """
        try:
            alpha_real = float(data.get("alphaReal", 0))
            alpha_imgn = float(data.get("alphaImgn", 0))
            beta_real = float(data.get("betaReal", 0))
            beta_imgn = float(data.get("betaImgn", 0))
            
            # Range validation
            if not all(-1 <= val <= 1 for val in [alpha_real, alpha_imgn, beta_real, beta_imgn]):
                return False, "All amplitude values must be between -1 and 1", {}
            
            # Check if all coefficients are zero
            if alpha_real == 0 and alpha_imgn == 0 and beta_real == 0 and beta_imgn == 0:
                recommended_values = {
                    'alphaReal': 0.5,
                    'alphaImgn': 0.5,
                    'betaReal': 0.5,
                    'betaImgn': 0.5
                }
                return False, "Invalid quantum state: Coefficients cannot be all zero. Recommended values are given in the form.", recommended_values
            
            # Normalization validation
            norm_squared = alpha_real**2 + alpha_imgn**2 + beta_real**2 + beta_imgn**2
            if abs(norm_squared - 1.0) > 0.0001:
                norm = math.sqrt(norm_squared)
                recommended_values = {
                    'alphaReal': round(alpha_real / norm, 8),
                    'alphaImgn': round(alpha_imgn / norm, 8),
                    'betaReal': round(beta_real / norm, 8),
                    'betaImgn': round(beta_imgn / norm, 8)
                }
                return False, f"Invalid quantum state: |α|² + |β|² must equal 1 (current: {norm_squared:.4f}). Recommended values are given in the form.", recommended_values
            
            # Name validation
            name = data.get("name", "").strip()
            if not name or len(name) > 45:
                return False, "Name must be 1-45 characters", {}
            
            # Symbol validation (before wrapping)
            symbol = data.get("symbol", "").strip()
            if not symbol or len(symbol) != 1:
                return False, "Symbol must be exactly 1 character", {}
            
            # Description validation
            description = data.get("description", "").strip()
            if not description or len(description) > 100:
                return False, "Description must be 1-100 characters", {}
            
            return True, "", {}
            
        except (ValueError, TypeError) as e:
            return False, f"Invalid data format: {str(e)}", {}

    def _to_sp_params(self, data: dict, include_id: bool = False) -> dict:
        """
        Map route data to stored procedure parameters.
        Args:
            data: Dictionary with keys like 'name', 'alphaReal', etc.
            include_id: Whether to include stateID (for edit operations)
        Returns: Dictionary with keys like 'p_name', 'p_alphaReal', etc.
        """
        # Wrap symbol with |>
        symbol = data.get("symbol", "").strip()
        wrapped_symbol = f"|{symbol}>"
        
        # For edit: p_stateID must be FIRST to match SP signature order
        if include_id:
            sp_params = {
                "p_stateID": data.get("stateID"),
                "p_name": data.get("name"),
                "p_alphaReal": data.get("alphaReal"),
                "p_alphaImgn": data.get("alphaImgn"),
                "p_betaReal": data.get("betaReal"),
                "p_betaImgn": data.get("betaImgn"),
                "p_symbol": wrapped_symbol,
                "p_description": data.get("description", "").strip()
            }
        else:
            sp_params = {
                "p_name": data.get("name"),
                "p_alphaReal": data.get("alphaReal"),
                "p_alphaImgn": data.get("alphaImgn"),
                "p_betaReal": data.get("betaReal"),
                "p_betaImgn": data.get("betaImgn"),
                "p_symbol": wrapped_symbol,
                "p_description": data.get("description", "").strip()
            }
        
        return sp_params

    @db_error_handler
    def show(self):
        """Retrieve all States entity records from the Database."""
        logger.info("START StatesUsecase.show")

        sql = self._build_select_all(table.STATES)
        result = self._execute(sql)

        data = [dict(row) for row in result.mappings().all()]
        data = self._decimal_to_str(
            data, [col.ALPHA_REAL, col.ALPHA_IMG, col.BETA_REAL, col.BETA_IMG]
        )
        logger.debug(f"Query result:{data}")

        logger.info("END StatesUsecase.show")
        return self._build_json_response(code.CODE_200, "OK", data)

    @db_error_handler
    def add(self, data: dict):
        """Add a new States entity record to the database."""
        logger.info("START StatesUsecase.add")
        logger.debug(f"Request Body:{data}")

        # Validate input
        is_valid, error_msg, recommended_values = self._validate_state_data(data)
        if not is_valid:
            logger.warning(f"Validation failed: {error_msg}")
            return self._build_json_response(code.CODE_400, error_msg, recommended_values if recommended_values else None)

        # Map to SP parameters
        sp_param = self._to_sp_params(data)
        
        sql = self._build_sp_call(sp.SP_INSERT_STATE, sp_param)
        logger.debug(f"SQL:{sql}")

        result = self._execute(sql, sp_param)
        row = result.mappings().fetchone()

        logger.info("END StatesUsecase.add")
        return self._build_json_response(row[col.CODE], row[col.MSG], None)

    @db_error_handler
    def edit(self, data: dict):
        """Update a States entity record in the database."""
        logger.info("START StatesUsecase.edit")
        logger.debug(f"Request Body:{data}")

        # Validate input
        is_valid, error_msg, recommended_values = self._validate_state_data(data)
        if not is_valid:
            logger.warning(f"Validation failed: {error_msg}")
            return self._build_json_response(code.CODE_400, error_msg, recommended_values if recommended_values else None)

        # Map to SP parameters (including ID for update)
        sp_param = self._to_sp_params(data, include_id=True)

        sql = self._build_sp_call(sp.SP_EDIT_STATE, sp_param)
        logger.debug(f"SQL:{sql}")

        result = self._execute(sql, sp_param)
        row = result.mappings().fetchone()

        logger.info("END StatesUsecase.edit")
        return self._build_json_response(row[col.CODE], row[col.MSG], None)

    @db_error_handler
    def delete(self, state_id: int):
        """Delete a States entity record from the database."""
        logger.info("START StatesUsecase.delete")

        sp_param = {"p_stateID": state_id}
        
        sql = self._build_sp_call(sp.SP_DELETE_STATE, sp_param)
        logger.debug(f"SQL:{sql}")

        result = self._execute(sql, sp_param)
        row = result.mappings().fetchone()

        logger.info("END StatesUsecase.delete")
        return self._build_json_response(row[col.CODE], row[col.MSG], None)
