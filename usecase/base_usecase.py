"""
App name: Quantum Computing Simulation
Description: Base usecase class providing shared database operations and utility methods
             inherited by all entity-specific usecase classes.
"""

from typing import Any, Optional, Literal, Dict, List
from utils.constants import Constants
from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause
from utils.logger import logger

table = Constants.Tables
col = Constants.Columns


class UsecaseBase:
    """
    Base class for all usecase classes.
    
    Provides common functionality for:
    - SQL execution with logging
    - Stored procedure call building
    - SELECT query building
    - Dropdown menu query building
    - JSON response formatting
    - Decimal to string conversion for UI display
    """

    def __init__(self, engine):
        self._engine = engine

    def _execute(self, sql, params: dict | None = None):
        """
        Func: Execute SQL and stored procedures
        Args:
            sql: SQL statement (e.g., SELECT * FROM table, CALL sp_xxx...)
            params: Optional dictionary of parameters for SQL or stored procedure
        Return:
            data (sqlalchemy.engine.CursorResult)
        """
        # Log the SQL being executed
        logger.debug(f"SQL EXECUTE: {str(sql)}")

        # Log parameters if present
        if params:
            logger.debug(f"SQL PARAMS: {params}")
            
        with self._engine.begin() as conn:
            if params:
                return conn.execute(sql, params)
            else:
                return conn.execute(sql)

    def _build_sp_call(self, sp_name: str, params: dict | None = None) -> TextClause:
        """
        Func: Build a sqlAlchemy SELECT statement for PostgreSQL functions.
        Args:
            * sp_name: The name of a stored function to be executed.
            * param: Input parameters
        Return:
            * the query string
        """
        if params:
            placeholders = ", ".join(f":{key}" for key in params.keys())
            sql = f"SELECT * FROM {sp_name}({placeholders})"
        else:
            sql = f"SELECT * FROM {sp_name}()"

        return text(sql)
    
    def _build_select_all(
            self,
            table_name: str, 
            order_by: Optional[str]=None, 
            sort_order: Optional[Literal["ASC", "DESC"]] = "ASC"
        )-> TextClause:
        """
        Func: Build the SELECT statement query
        Args:
            * table_name: the name of the table
            * order_by: the column name to sort by
            * sort_order: ascending or descending
        Return: the query string
        Example:
            'SELECT * FROM "Shots" ORDER BY "shotID" ASC;'
        """
        sql = f'SELECT * FROM "{table_name}"'

        # ORDER BY is optional
        if order_by:
            sql += f' ORDER BY "{order_by}" {sort_order}'

        return text(sql)
    
    def _build_state_symbol_dropdown(self)-> TextClause:
        """
        Func: Build the SELECT statement for the state symbol drop down menu.
        Args: -
        Return: the query string
        Example:
            SELECT "stateID", CONCAT("name", ' (', "symbol", ')') AS name_symbol FROM "States";
            Result: "zero_state (|0>)"
        """
        sql = f'SELECT "{col.STATE_ID}", CONCAT("{col.NAME}", \' (\', "{col.SYMBOL}", \')\') AS name_symbol FROM "{table.STATES}"'
        return text(sql)
    
    def _build_sim_id_dropdown(self)-> TextClause:
        """
        Func: Build the SELECT statement for the simulationId drop down menu.
        Args: -
        Return: the query string
        Example:
            simID:100 (Gate:|X|, State:|+>)
        """
        sql = f'''
            SELECT
                "{table.SIMULATIONS}"."{col.SIM_ID}" AS "simID",
                CONCAT('simID:', "{table.SIMULATIONS}"."{col.SIM_ID}", ' (Gate:', "{table.GATES}"."{col.SYMBOL}", ',State:', "{table.STATES}"."{col.SYMBOL}", ')') AS choice
            FROM "{table.SIMULATIONS}"
            INNER JOIN "{table.GATES}" 
            ON "{table.SIMULATIONS}"."{col.GATE_ID}" = "{table.GATES}"."{col.GATE_ID}"
            INNER JOIN "{table.STATES}"
            ON "{table.SIMULATIONS}"."{col.STATE_ID}" = "{table.STATES}"."{col.STATE_ID}"
            ORDER BY "{table.SIMULATIONS}"."{col.SIM_ID}" ASC
            '''
        return text(sql)

    def _build_json_response(self, status_code: int, message: str, data: Optional[Any] = None) -> dict:
        """
        Func: Create a response dict
        Args:
            * status_code: HTTP status code
            * message: response message
            * data: query result
        Example:
        {
            "status_code": 200,
            "message": "Success",
            "data": {...}
        }
        """
        result: dict = {
            "status_code": status_code,
            "context": {
                "message": message
            }
        }

        if data is not None:
            result["context"]["data"] = data

        return result

    def _build_gate_symbol_dropdown(self)-> TextClause:
        """
        Func: Build the SELECT statement for the gate symbol drop down menu.
        Args: -
        Return: the query string
        Example:
            SELECT "gateID", CONCAT("name", ' (', "symbol", ')') AS name_symbol FROM "Gates";
            Result: "X Gate (|X|)"
        """
        sql = f'SELECT "{col.GATE_ID}", CONCAT("{col.NAME}", \' (\', "{col.SYMBOL}", \')\') AS name_symbol FROM "{table.GATES}"'
        return text(sql)
    
    def _decimal_to_str(self, data: List[Dict[str, Any]], keys: List[str]) -> List[Dict[str, Any]]:
        """
        Func: Convert specified Decimal fields in a list of dicts to fixed-point 8-digit strings.
        Note: 
            The number "0.000000008 DECIMAL(9,8)" is treated as '0E-8' in Python's internal representation 
            and is displayed as is in the UI, 
            so it is necessary to convert the decimal type to a string type before passing it to the UI.
        """
        formatted_data = []
        for row in data:
            row_copy = dict(row)
            for key in keys:
                if key in row_copy and row_copy[key] is not None:
                    row_copy[key] = f"{row_copy[key]:.8f}"
            formatted_data.append(row_copy)

        return formatted_data