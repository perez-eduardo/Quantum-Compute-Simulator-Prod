"""
App name: Quantum Computing Simulation
Description: Usecase class for managing operations on the application's homepage,
             including database reset functionality.
"""

from usecase.base_usecase import UsecaseBase
from utils.constants import Constants
from utils.logger import logger

sp = Constants.StoredProcedures
col = Constants.Columns


class IndexUsecase(UsecaseBase):
    """
    A usecase class responsible for managing the operations performed 
    on the application's top (home) page.
    """

    def __init__(self, engine):
        super().__init__(engine)

    def reset(self) -> dict:
        """
        Func: Reset the database and insert initial sample values
        Args: -
        Return: The dict of the status code, response message
        """
        logger.info("START IndexUsecase.reset")

        # Create a SQL statement
        sql = self._build_sp_call(sp.SP_LOAD_QCDB)

        # Execute the stored procedure
        result = self._execute(sql)
        row = result.mappings().fetchone()
        logger.debug(f"SP result:{row}")

        logger.info("END IndexUsecase.reset")
        return self._build_json_response(row[col.CODE], row[col.MSG], None)
