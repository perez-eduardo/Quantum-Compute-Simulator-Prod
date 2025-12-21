"""
App name: Quantum Computing Simulation
Description: Application-wide constants for table names, stored procedures,
             HTTP response codes, and database column names.
"""


class Constants:
    """
    Top-level container for all application constants.
    Organized into nested classes by category.
    """

    class Tables:
        """Database table names."""

        GATES = "Gates"
        STATES = "States"
        SIMULATIONS = "Simulations"
        SHOTS = "Shots"

    class StoredProcedures:
        """Stored procedure names."""

        # Top page
        SP_LOAD_QCDB = "sp_load_qcdb"

        # States Entity
        SP_INSERT_STATE = "sp_insert_state"
        SP_DELETE_STATE = "sp_delete_state"
        SP_EDIT_STATE = "sp_edit_state"

        # Simulations Entity
        SP_INSERT_SIMULATION = "sp_insert_simulation"
        SP_DELETE_SIMULATION = "sp_delete_simulation"

        # Shots Entity
        SP_INSERT_SHOT = "sp_insert_shot"

    class ResponseCode:
        """HTTP response status codes used by the application."""

        CODE_200 = 200  # OK
        CODE_201 = 201  # Created
        CODE_202 = 202  # Accepted (processing started, not yet complete)
        CODE_204 = 204  # No Content (successful delete)
        CODE_400 = 400  # Bad Request
        CODE_404 = 404  # Not Found
        CODE_409 = 409  # Conflict (unique constraint violation)
        CODE_500 = 500  # Internal Server Error

    class Columns:
        """
        Database column names.
        Used for building dynamic SQL queries and accessing result dictionaries.
        """

        # Response attributes
        CODE = "code"
        MSG = "message"

        # Primary keys
        STATE_ID = "stateID"
        GATE_ID = "gateID"
        SIM_ID = "simID"
        SHOT_ID = "shotID"

        # Common columns
        NAME = "name"
        SYMBOL = "symbol"

        # Amplitude columns (used in States and Shots)
        ALPHA_REAL = "alphaReal"
        ALPHA_IMG = "alphaImgn"
        BETA_REAL = "betaReal"
        BETA_IMG = "betaImgn"

        # Shots specific
        OUTPUT_STATE = "outputState"
