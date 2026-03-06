"""
Research Synthesizer -- Web Research + Data Synthesis

Orchestrates qualitative web research (search, think tank analysis, news)
and combines with structured data snapshots from the collector.

This is the agent-facing component -- it provides the research brief
that the paper pipeline drafts from.

Usage:
    synthesizer = ResearchSynthesizer()
    brief = await synthesizer.synthesize(
        snapshot=collector_output,
        topic="iran_threat_assessment",
        research_queries=["IRGC posture", "think tank assessments", ...]
    )

Pipeline:
    1. Takes structured data snapshot from collector
    2. Generates research queries based on topic + data signals
    3. Executes web research (agent-driven)
    4. Combines structured data + web research into unified brief
    5. Outputs research brief (markdown) for paper pipeline

TODO: Implement. See docs/BUILD.md for specification.
"""
