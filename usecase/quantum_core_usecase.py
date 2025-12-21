"""
Citation (IBM Qiskit)
* Citation Scope: Gate matrix definitions and state vector transformation logic.
* Date: 11/26/2025
* Originality: Knowledge base for quantum gate mathematics. Implementation code is original.
* Source URL: https://learning.quantum.ibm.com/

Quantum Core Utility Module

This module provides quantum gate matrices and functions for simulating
quantum state transformations and measurement shots.

Supported standard gates: X (Pauli-X), Y (Pauli-Y), Z (Pauli-Z), H (Hadamard), I (Identity)
Custom gates use random noise logic for shot generation.
"""

import numpy as np
from typing import List, Dict

from utils.logger import logger


# Standard quantum gate matrices - keyed by single letter symbol
GATE_MATRICES = {
    "X": np.array([[0, 1], [1, 0]], dtype=complex),              # Pauli-X (Bit flip)
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),           # Pauli-Y (Bit + phase flip)
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),             # Pauli-Z (Phase flip)
    "H": np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),# Hadamard
    "I": np.array([[1, 0], [0, 1]], dtype=complex),              # Identity (No operation)
}

# List of supported gate symbols (for validation)
SUPPORTED_GATES = list(GATE_MATRICES.keys())


def get_gate_matrix(gate_symbol: str) -> np.ndarray:
    """
    Get the matrix representation of a quantum gate.
    
    Args:
        gate_symbol: Single letter symbol of the gate (X, Y, Z, H, I)
        
    Returns:
        2x2 complex numpy array representing the gate
        
    Raises:
        ValueError: If gate_symbol is not supported
    """
    if gate_symbol not in GATE_MATRICES:
        raise ValueError(f"Unsupported gate: {gate_symbol}. Supported gates: {SUPPORTED_GATES}")
    return GATE_MATRICES[gate_symbol]


def apply_gate(state: np.ndarray, gate_symbol: str) -> np.ndarray:
    """
    Apply a quantum gate to a state vector.
    
    Args:
        state: 2-element complex numpy array [α, β] representing |ψ⟩ = α|0⟩ + β|1⟩
        gate_symbol: Single letter symbol of the gate to apply
        
    Returns:
        New state vector after gate application
    """
    gate = get_gate_matrix(gate_symbol)
    return gate @ state


def build_state_vector(alpha_real: float, alpha_imgn: float, 
                       beta_real: float, beta_imgn: float) -> np.ndarray:
    """
    Build a quantum state vector from amplitude components.
    
    Args:
        alpha_real: Real part of α (amplitude for |0⟩)
        alpha_imgn: Imaginary part of α
        beta_real: Real part of β (amplitude for |1⟩)
        beta_imgn: Imaginary part of β
        
    Returns:
        2-element complex numpy array [α, β]
    """
    return np.array([
        complex(alpha_real, alpha_imgn),
        complex(beta_real, beta_imgn)
    ], dtype=complex)


def generate_shots(alpha_real: float, alpha_imgn: float,
                   beta_real: float, beta_imgn: float,
                   gate_symbol: str, num_shots: int) -> List[Dict]:
    """
    Generate measurement shots after applying a quantum gate to an initial state.
    
    This function:
    1. Builds the initial state vector from amplitudes
    2. Applies the specified quantum gate
    3. Generates num_shots measurements with small noise variations
    
    Args:
        alpha_real: Real part of initial α
        alpha_imgn: Imaginary part of initial α
        beta_real: Real part of initial β
        beta_imgn: Imaginary part of initial β
        gate_symbol: Single letter symbol of the gate to apply (X, Y, Z, H, I)
        num_shots: Number of measurement shots to generate
        
    Returns:
        List of dicts, each containing:
            - alphaReal, alphaImgn, betaReal, betaImgn: Final state amplitudes (with noise)
            - outputState: Measurement result (0 or 1)
    """
    logger.info(f"START generate_shots: gate={gate_symbol}, num_shots={num_shots}")
    
    # Build initial state vector
    initial_state = build_state_vector(alpha_real, alpha_imgn, beta_real, beta_imgn)
    logger.debug(f"Initial state: {initial_state}")
    
    # Apply quantum gate
    final_state = apply_gate(initial_state, gate_symbol)
    logger.debug(f"Final state after {gate_symbol}: {final_state}")
    
    # Extract final amplitudes
    final_alpha = final_state[0]
    final_beta = final_state[1]
    
    # Calculate probability of measuring |0⟩
    prob_zero = abs(final_alpha) ** 2
    logger.debug(f"Probability of |0⟩: {prob_zero:.6f}")
    
    # Generate measurement shots
    shots = []
    for i in range(num_shots):
        # Add small measurement noise to simulate real quantum behavior
        variation = np.random.uniform(-0.00005, 0.00005)
        
        shot_alpha_real = final_alpha.real + variation
        shot_alpha_imgn = final_alpha.imag + variation
        shot_beta_real = final_beta.real + variation
        shot_beta_imgn = final_beta.imag + variation
        
        # Probabilistic measurement outcome
        output_state = 0 if np.random.random() < prob_zero else 1
        
        shots.append({
            "alphaReal": shot_alpha_real,
            "alphaImgn": shot_alpha_imgn,
            "betaReal": shot_beta_real,
            "betaImgn": shot_beta_imgn,
            "outputState": output_state
        })
    
    logger.info(f"END generate_shots: generated {len(shots)} shots")
    return shots


def generate_shots_random_noise(alpha_real: float, alpha_imgn: float,
                                 beta_real: float, beta_imgn: float,
                                 num_shots: int) -> List[Dict]:
    """
    Generate measurement shots using random noise logic.
    Used for custom/non-standard gates that don't have defined matrix operations.
    
    This function:
    1. Takes the initial state amplitudes
    2. Adds small random noise to simulate measurement variation
    3. Calculates probability from the noisy amplitudes
    4. Generates probabilistic output states
    
    Args:
        alpha_real: Real part of initial α
        alpha_imgn: Imaginary part of initial α
        beta_real: Real part of initial β
        beta_imgn: Imaginary part of initial β
        num_shots: Number of measurement shots to generate
        
    Returns:
        List of dicts, each containing:
            - alphaReal, alphaImgn, betaReal, betaImgn: State amplitudes (with noise)
            - outputState: Measurement result (0 or 1)
    """
    logger.info(f"START generate_shots_random_noise: num_shots={num_shots}")
    logger.debug(f"Initial amplitudes: alpha=({alpha_real}, {alpha_imgn}), beta=({beta_real}, {beta_imgn})")
    
    shots = []
    for i in range(num_shots):
        # Add small random noise to amplitudes
        variation = np.random.uniform(-0.00005, 0.00005)
        
        shot_alpha_real = alpha_real + variation
        shot_alpha_imgn = alpha_imgn + variation
        shot_beta_real = beta_real + variation
        shot_beta_imgn = beta_imgn + variation
        
        # Calculate probability of measuring |0⟩ from noisy amplitudes
        prob_zero = shot_alpha_real ** 2 + shot_alpha_imgn ** 2
        
        # Probabilistic measurement outcome
        output_state = 0 if np.random.random() < prob_zero else 1
        
        shots.append({
            "alphaReal": shot_alpha_real,
            "alphaImgn": shot_alpha_imgn,
            "betaReal": shot_beta_real,
            "betaImgn": shot_beta_imgn,
            "outputState": output_state
        })
    
    logger.info(f"END generate_shots_random_noise: generated {len(shots)} shots")
    return shots


def is_supported_gate(gate_symbol: str) -> bool:
    """
    Check if a gate symbol is supported for quantum calculations.
    
    Args:
        gate_symbol: Single letter symbol of the gate to check
        
    Returns:
        True if supported, False otherwise
    """
    return gate_symbol in SUPPORTED_GATES