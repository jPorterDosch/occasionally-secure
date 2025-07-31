# Occasionally Secure: A Comparative Analysis of Code Generation Assistants

**Paper**: [Occasionally Secure: A Comparative Analysis of Code Generation Assistants](https://arxiv.org/abs/2402.00689)

This repository accompanies the paper and contains model outputs and evaluation scripts for benchmarking code generation assistants on software security and reliability tasks.

## Overview

We evaluate a range of web-facing LLMs using a set of security-related programming tasks. Models are tested across two personas: a security-minded engineer and a general-purpose software engineer. Performance is measured based on:

- Number of revisions required to fix model-generated code
- Cyclomatic complexity
- Syntax, functionality, and semantic reliability

Model responses were manually collected via public web interfaces and are organized by model and persona type. This repository provides the data and scripts used for analysis.

## Repository Structure

.
├── Complexity/
│ └── Scripts for measuring cyclomatic complexity
├── Consistency/
│ └── Scripts for evaluating reliability (syntax, functionality, semantics)
├── Gemini/
│ ├── Gemini/
│ │ ├── Security Persona/
│ │ ├── Software Engineer Persona/
│ │ ├── Security Reliability/
│ │ └── Software Reliability/
│ └── Gemini_reasoning/
| └── [Organized similarly to Gemini by persona and reliability type]
├── [Other LLM folders]/
│ └── [Organized similarly by persona and reliability type]
├── README.md


## Data Collection

Model generations were collected manually through browser interactions with LLMs. Evaluation data is stored in tabular form (currently as a Google Sheet) and includes:

- Number of revisions required
- Execution and correction time
- Reliability ratings (syntax, functionality, semantics)

An export of the cleaned dataset will be added to this repository in a future update.

## Evaluation

### Cyclomatic Complexity

To compute the complexity of model-generated code samples, use the scripts in the `Complexity/` directory.

Example usage:
```bash
python Complexity/com.py
```
Reliability Evaluation

The Consistency/ directory contains scripts to assess code reliability across syntax and functionality. These evaluations are currently manual or semi-automated and aligned with the schema described in the paper.
Future Additions

    Prompt templates and persona definitions

    CSV export of the evaluation spreadsheet

    Additional aggregate analysis scripts
