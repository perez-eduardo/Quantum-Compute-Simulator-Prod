"""
App name: Quantum Computing Simulation
Description: Usecase class for managing read and filter operations on the Measurement Shots entity.
"""

from usecase.base_usecase import UsecaseBase
from usecase.shots_graph_usecase import ShotsGraphUsecase
from utils.constants import Constants
from utils.logger import logger
from utils.decorators import db_error_handler

from sqlalchemy import text

table = Constants.Tables
col = Constants.Columns
code = Constants.ResponseCode


class ShotsUsecase(UsecaseBase):
    """
    A usecase class responsible for managing the operations performed 
    on the application's Quantum Shots page.
    """

    def __init__(self, engine):
        super().__init__(engine)
        self.graph_usecase = ShotsGraphUsecase()
    
    @db_error_handler
    def show(self):
        """
        Func: Show the shots page without any simulation selected.
              Returns only the simulation dropdown data and a placeholder graph.
        Note: No shots data is returned - user must select a simulation first.
        """
        logger.info("START ShotsUsecase.show")

        # SELECT statement for the filter drop down
        sql = self._build_sim_id_dropdown()
        result = self._execute(sql)
        sim_data = [dict(row) for row in result.mappings().all()]
        logger.debug(f"sim_data:{sim_data}")

        # Generate placeholder graph
        graph_result = self.graph_usecase.generate_placeholder()

        data = {
            "shot_data": [],  # Empty - no simulation selected
            "sim_data": sim_data,
            "graph_image": graph_result['image'],
            "graph_interpretation": graph_result['interpretation'],
            "sim_selected": False  # Flag to indicate no simulation is selected
        }

        logger.info("END ShotsUsecase.show")
        return self._build_json_response(code.CODE_200, "OK", data)

    @db_error_handler
    def filter(self, sim_id: int):
        """
        Func: Filter shots by simID and return shots data with visualization graph.
        Args:
            * sim_id: simID to filter by
        """
        logger.info("START ShotsUsecase.filter")

        # Filter shots by simulation ID
        sql = text(f'SELECT * FROM "{table.SHOTS}" WHERE "{col.SIM_ID}" = {sim_id};')
        result = self._execute(sql)
        shot_data = [dict(row) for row in result.mappings().all()]
        
        # Keep original data for graph generation (before string conversion)
        shot_data_for_graph = shot_data.copy()
        
        # Format decimal data for display
        shot_data = self._decimal_to_str(
            shot_data, 
            [col.ALPHA_REAL, col.ALPHA_IMG, col.BETA_REAL, col.BETA_IMG]
        )
        logger.debug(f"shot_data:{shot_data}")

        # Get simulation details (state symbol and gate symbol)
        sql = text(f"""
            SELECT s.symbol AS state_symbol, g.symbol AS gate_symbol
            FROM "{table.SIMULATIONS}" sim
            JOIN "{table.STATES}" s ON sim."stateID" = s."stateID"
            JOIN "{table.GATES}" g ON sim."gateID" = g."gateID"
            WHERE sim."simID" = {sim_id};
        """)
        result = self._execute(sql)
        sim_details = result.mappings().fetchone()
        
        state_symbol = sim_details['state_symbol'] if sim_details else None
        gate_symbol = sim_details['gate_symbol'] if sim_details else None
        logger.debug(f"state_symbol:{state_symbol}, gate_symbol:{gate_symbol}")

        # SELECT statement for the filter drop down
        sql = self._build_sim_id_dropdown()
        result = self._execute(sql)
        sim_data = [dict(row) for row in result.mappings().all()]
        logger.debug(f"sim_data:{sim_data}")

        # Generate histogram graph with simulation details
        graph_result = self.graph_usecase.generate_histogram(
            shot_data_for_graph, 
            sim_id,
            state_symbol,
            gate_symbol
        )

        data = {
            "shot_data": shot_data,
            "sim_data": sim_data,
            "graph_image": graph_result['image'],
            "graph_interpretation": graph_result['interpretation'],
            "sim_selected": True,  # Flag to indicate a simulation is selected
            "current_sim_id": sim_id  # Pass the current sim_id for the dropdown
        }

        logger.info("END ShotsUsecase.filter")
        return self._build_json_response(code.CODE_200, "OK", data)
