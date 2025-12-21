-- ===== Overview =====
-- App name: Quantum Computing Simulation
-- Description: PostgreSQL stored functions for CRUD operations

-- -----------------------------------------------------
-- Quantum States
-- -----------------------------------------------------

-- Insert a new state
CREATE OR REPLACE FUNCTION sp_insert_state(
    p_name VARCHAR(45),
    p_alphaReal NUMERIC(9,8),
    p_alphaImgn NUMERIC(9,8),
    p_betaReal NUMERIC(9,8),
    p_betaImgn NUMERIC(9,8),
    p_symbol VARCHAR(45),
    p_description VARCHAR(100)
)
RETURNS TABLE(code INTEGER, message VARCHAR) AS $$
BEGIN
    -- Check unique constraint on name (case-insensitive)
    IF EXISTS (SELECT 1 FROM "States" WHERE LOWER("name") = LOWER(p_name)) THEN
        RETURN QUERY SELECT 409, '[ERROR] The name attribute violates the unique constraint.'::VARCHAR;
        RETURN;
    END IF;

    -- Check unique constraint on symbol (case-insensitive)
    IF EXISTS (SELECT 1 FROM "States" WHERE LOWER("symbol") = LOWER(p_symbol)) THEN
        RETURN QUERY SELECT 409, '[ERROR] The symbol attribute violates the unique constraint.'::VARCHAR;
        RETURN;
    END IF;

    -- Insert
    INSERT INTO "States" ("name", "alphaReal", "alphaImgn", "betaReal", "betaImgn", "symbol", "description")
    VALUES (p_name, p_alphaReal, p_alphaImgn, p_betaReal, p_betaImgn, p_symbol, p_description);

    RETURN QUERY SELECT 201, 'Created'::VARCHAR;
END;
$$ LANGUAGE plpgsql;


-- Edit a state
CREATE OR REPLACE FUNCTION sp_edit_state(
    p_stateID INTEGER,
    p_name VARCHAR(45),
    p_alphaReal NUMERIC(9,8),
    p_alphaImgn NUMERIC(9,8),
    p_betaReal NUMERIC(9,8),
    p_betaImgn NUMERIC(9,8),
    p_symbol VARCHAR(45),
    p_description VARCHAR(100)
)
RETURNS TABLE(code INTEGER, message VARCHAR) AS $$
BEGIN
    -- Check if state exists
    IF NOT EXISTS (SELECT 1 FROM "States" WHERE "stateID" = p_stateID) THEN
        RETURN QUERY SELECT 404, '[ERROR] Not Found. A record with the specified ID does not exist.'::VARCHAR;
        RETURN;
    END IF;

    -- Protection: Standard states (IDs 1-6) cannot be modified
    IF p_stateID <= 6 THEN
        RETURN QUERY SELECT 403, '[ERROR] Forbidden. Standard quantum states cannot be modified.'::VARCHAR;
        RETURN;
    END IF;

    -- No changes check
    IF EXISTS (
        SELECT 1 FROM "States" 
        WHERE "stateID" = p_stateID 
        AND "name" = p_name 
        AND "symbol" = p_symbol 
        AND "alphaReal" = p_alphaReal 
        AND "alphaImgn" = p_alphaImgn 
        AND "betaReal" = p_betaReal 
        AND "betaImgn" = p_betaImgn
        AND "description" = p_description
    ) THEN
        RETURN QUERY SELECT 200, 'OK'::VARCHAR;
        RETURN;
    END IF;

    -- Check unique constraint on name (case-insensitive, excluding current record)
    IF EXISTS (SELECT 1 FROM "States" WHERE LOWER("name") = LOWER(p_name) AND "stateID" <> p_stateID) THEN
        RETURN QUERY SELECT 409, '[ERROR] Conflict. The name attribute must be unique.'::VARCHAR;
        RETURN;
    END IF;

    -- Check unique constraint on symbol (case-insensitive, excluding current record)
    IF EXISTS (SELECT 1 FROM "States" WHERE LOWER("symbol") = LOWER(p_symbol) AND "stateID" <> p_stateID) THEN
        RETURN QUERY SELECT 409, '[ERROR] Conflict. The symbol attribute must be unique.'::VARCHAR;
        RETURN;
    END IF;

    -- Update
    UPDATE "States"
    SET "name" = p_name,
        "alphaReal" = p_alphaReal,
        "alphaImgn" = p_alphaImgn,
        "betaReal" = p_betaReal,
        "betaImgn" = p_betaImgn,
        "symbol" = p_symbol,
        "description" = p_description
    WHERE "stateID" = p_stateID;

    RETURN QUERY SELECT 200, 'OK'::VARCHAR;
END;
$$ LANGUAGE plpgsql;


-- Delete a state
CREATE OR REPLACE FUNCTION sp_delete_state(p_stateID INTEGER)
RETURNS TABLE(code INTEGER, message VARCHAR) AS $$
BEGIN
    -- Check if state exists
    IF NOT EXISTS (SELECT 1 FROM "States" WHERE "stateID" = p_stateID) THEN
        RETURN QUERY SELECT 404, '[ERROR] Not Found. A record with the specified ID does not exist.'::VARCHAR;
        RETURN;
    END IF;

    -- Protection: Standard states (IDs 1-6) cannot be deleted
    IF p_stateID <= 6 THEN
        RETURN QUERY SELECT 403, '[ERROR] Forbidden. Standard quantum states cannot be deleted.'::VARCHAR;
        RETURN;
    END IF;

    DELETE FROM "States" WHERE "stateID" = p_stateID;

    RETURN QUERY SELECT 204, 'A record with the specified ID has been deleted.'::VARCHAR;
END;
$$ LANGUAGE plpgsql;


-- -----------------------------------------------------
-- Simulations
-- -----------------------------------------------------

-- Insert a simulation
CREATE OR REPLACE FUNCTION sp_insert_simulation(p_stateID INTEGER, p_gateID INTEGER)
RETURNS TABLE(code INTEGER, message VARCHAR, "simID" INTEGER) AS $$
DECLARE
    v_simID INTEGER;
BEGIN
    -- Check if state exists
    IF NOT EXISTS (SELECT 1 FROM "States" WHERE "stateID" = p_stateID) THEN
        RETURN QUERY SELECT 404, '[ERROR] Not Found. The specified state does not exist.'::VARCHAR, NULL::INTEGER;
        RETURN;
    END IF;

    -- Check if gate exists
    IF NOT EXISTS (SELECT 1 FROM "Gates" WHERE "gateID" = p_gateID) THEN
        RETURN QUERY SELECT 404, '[ERROR] Not Found. The specified gate does not exist.'::VARCHAR, NULL::INTEGER;
        RETURN;
    END IF;

    -- Insert and get the new ID
    INSERT INTO "Simulations" ("stateID", "gateID")
    VALUES (p_stateID, p_gateID)
    RETURNING "Simulations"."simID" INTO v_simID;

    RETURN QUERY SELECT 201, 'Created'::VARCHAR, v_simID;
END;
$$ LANGUAGE plpgsql;


-- Delete a simulation
CREATE OR REPLACE FUNCTION sp_delete_simulation(p_simID INTEGER)
RETURNS TABLE(code INTEGER, message VARCHAR) AS $$
BEGIN
    -- Check if simulation exists
    IF NOT EXISTS (SELECT 1 FROM "Simulations" WHERE "simID" = p_simID) THEN
        RETURN QUERY SELECT 404, '[ERROR] Not Found. A record with the specified ID does not exist.'::VARCHAR;
        RETURN;
    END IF;

    -- Shots are deleted automatically via CASCADE
    DELETE FROM "Simulations" WHERE "simID" = p_simID;

    RETURN QUERY SELECT 204, 'Deleted'::VARCHAR;
END;
$$ LANGUAGE plpgsql;


-- -----------------------------------------------------
-- Shots
-- -----------------------------------------------------

-- Insert a shot
CREATE OR REPLACE FUNCTION sp_insert_shot(
    p_simID INTEGER,
    p_alphaReal NUMERIC(9,8),
    p_alphaImgn NUMERIC(9,8),
    p_betaReal NUMERIC(9,8),
    p_betaImgn NUMERIC(9,8),
    p_outputState INTEGER
)
RETURNS TABLE(code INTEGER, message VARCHAR) AS $$
BEGIN
    -- Check if simulation exists
    IF NOT EXISTS (SELECT 1 FROM "Simulations" WHERE "simID" = p_simID) THEN
        RETURN QUERY SELECT 404, '[ERROR] Not Found. The specified simulation does not exist.'::VARCHAR;
        RETURN;
    END IF;

    INSERT INTO "Shots" ("simID", "alphaReal", "alphaImgn", "betaReal", "betaImgn", "outputState")
    VALUES (p_simID, p_alphaReal, p_alphaImgn, p_betaReal, p_betaImgn, p_outputState);

    RETURN QUERY SELECT 201, 'Created'::VARCHAR;
END;
$$ LANGUAGE plpgsql;