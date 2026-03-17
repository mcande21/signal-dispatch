"""Signal Dispatch delta engine.

Polls data sources, computes deltas against prior state, detects threshold
breaches, and writes results to disk for the editorial pipeline.

Entry point: python -m src.delta.daemon
"""
