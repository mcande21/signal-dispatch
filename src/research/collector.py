"""
Research Collector -- Data Collection Pipeline

Wraps the prediction-markets project's adapters to collect structured data
snapshots for each newsletter issue. Does NOT duplicate adapter code.

Usage:
    collector = ResearchCollector(pm_root="/path/to/prediction-markets")
    snapshot = await collector.collect(topic="iran", sources=["ooni", "bonbast", "ofac"])

Pipeline:
    1. Reads sources.yaml for available adapters
    2. Runs specified adapters via prediction-markets CLI (subprocess)
    3. Collects output JSON into a unified research snapshot
    4. Saves snapshot to content/research/{issue_date}/

TODO: Implement. See docs/BUILD.md for specification.
"""
