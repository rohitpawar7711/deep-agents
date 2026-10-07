---
name: report-writing
description: Structured report writing, synthesis, executive summaries, technical documentation, and formal delivery standards for DeepAgents. Use whenever producing a final report, synthesizing research findings, documenting architecture or code reviews, or answering complex user queries with a structured written report.
license: MIT
compatibility: Markdown, GitHub Flavored Markdown, DeepAgents Artifacts
allowed-tools: read_file write_file edit_file list_directory
---

# Report Writing & Synthesis Skill

## Overview
This skill establishes standardized formats, structural blueprints, and quality guidelines for generating high-impact, professional reports whenever DeepAgents answers complex user queries, conducts codebase investigations, analyzes architectures, or synthesizes research findings.

Instead of outputting unstructured or fragmented text, DeepAgents should utilize this skill to deliver structured, readable, and actionable reports that stakeholders can immediately review, share, or persist to disk.

---

## When to Use This Skill
- Delivering the final answer or summary of a multi-step DeepAgent execution.
- Conducting codebase audits, architectural reviews, or dependency analyses.
- Formulating Root Cause Analysis (RCA) and post-incident investigation reports.
- Synthesizing deep web research, benchmark comparisons, or technology evaluations.
- Writing persistent documentation files to the repository (e.g., in `/reports/`, `/projects/`, or memory files).
- Presenting complex technical concepts with executive summaries, diagrams, tables, and action items.

---

## Skill Navigation & Progressive Disclosure
For deep, context-specific guidance, consult the companion files in this skill directory:

1. **[`instruction.md`](./instruction.md)**:
   - Report lifecycle and trigger criteria (inline response vs saved report file).
   - Structural blueprint: Metadata header, Executive Summary, Problem Statement, Deep Dive / Methodology, Key Findings, Actionable Recommendations, and Appendix.
   - Visual standards: Markdown tables, Mermaid workflow diagrams, and GitHub-style callouts (`[!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`).
   - Tone, objectivity, and evidence citation standards.
   - Persistence guidelines for DeepAgents memory and report archival.

2. **[`examples.md`](./examples.md)**:
   - Production-grade report templates:
     - **Template 1**: Technical Architecture & Codebase Evaluation Report.
     - **Template 2**: Root Cause Analysis (RCA) & Bug Investigation Report.
     - **Template 3**: Comprehensive Technology & Benchmark Comparison Report.
     - **Template 4**: Executive Decision Brief (high-level leadership summary).

---

## Core Report Writing Principles
1. **BLUF (Bottom Line Up Front)**: Always state the core conclusion, recommendation, or result in the Executive Summary before detailing the evidence.
2. **Actionable & Specific**: Ensure findings lead to concrete, numbered next steps with assigned priorities.
3. **Evidence-Based**: Back assertions with file paths, line numbers, test outputs, or benchmark metrics.
4. **Structured Formatting**: Use headers, bullet points, callout boxes, and comparative tables rather than long uninterrupted walls of text.
5. **Durable Persistence**: When the findings have lasting project value, write the report to disk (e.g., `reports/YYYY-MM-DD-<topic>.md`) and update project memory (`Agents.md`).
