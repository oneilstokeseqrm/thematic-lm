# Product Overview: Thematic-LM

## What is Thematic-LM?

Thematic-LM is a multi-agent LLM system that automates large-scale thematic analysis of unstructured text data. It processes qualitative feedback from sources like social media posts, emails, and customer interactions through a two-stage pipeline: inductive coding followed by theme development.

## Purpose

Process unstructured text data for EQ CRM by:
- Generating descriptive codes for text segments with supporting quotes
- Synthesizing codes into higher-level themes
- Maintaining an adaptive codebook that evolves with new data
- Providing scalable analysis that combines qualitative depth with computational efficiency

## Key Capabilities

- **Inductive Coding with Multiple Perspectives**: Deploy multiple coder agents with different identity perspectives to capture diverse interpretations of the same data
- **Adaptive Codebook Management**: Automatically merge, update, and version codes as new data arrives; track code usage with decay scoring
- **Scalable Theme Generation**: Synthesize hundreds of codes into coherent themes using LLM-based aggregation with automatic compression for large codebooks
- **Incremental Analysis**: Process only new interactions while building on existing codebooks, with configurable thresholds for full theme regeneration
- **Cost-Aware Processing**: Estimate analysis costs upfront and enforce budget limits before execution

## Target Users

- **Research Teams**: Analyzing qualitative data at scale with multiple analytical perspectives
- **Product Analysts**: Processing user feedback and feature requests to identify patterns
- **CX Teams**: Analyzing customer interactions, support tickets, and feedback across channels
- **Social Listening Teams**: Monitoring and analyzing social media conversations for emerging themes

## Analysis Workflow

1. Client submits analysis request via API with account ID and date range
2. System estimates cost and validates against budget ceiling
3. Coding stage: Multiple coder agents analyze interactions and generate codes with quotes
4. Code aggregation: Merge duplicate codes and update adaptive codebook
5. Theme development: Synthesize codes into higher-level themes with supporting evidence
6. Results delivered via polling or event stream with full traceability to source text
