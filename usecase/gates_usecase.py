"""
App name: Quantum Computing Simulation
Description: Usecase class for displaying quantum gates (read-only).
             Gates are predefined standard quantum operations.
"""

from usecase.base_usecase import UsecaseBase
from utils.constants import Constants
from utils.logger import logger
from utils.decorators import db_error_handler

table = Constants.Tables
code = Constants.ResponseCode


class GatesUsecase(UsecaseBase):
    """
    A usecase class responsible for displaying quantum gates.
    Gates are read-only as they represent standard quantum operations.
    """

    def __init__(self, engine):
        super().__init__(engine)
    
    @db_error_handler
    def show(self):
        """
        Func: A method to retrieve all Gates entity records from the Database.
        Note: This method uses the SELECT statements instead of stored procedures.
        """
        logger.info("START GatesUsecase.show")

        # Create a SQL statement
        sql = self._build_select_all(table.GATES)

        # Execute the SELECT statement
        result = self._execute(sql)
        data = [dict(row) for row in result.mappings().all()]
        logger.debug(f"Query result:{data}")

        logger.info("END GatesUsecase.show")
        return self._build_json_response(code.CODE_200, "OK", data)
