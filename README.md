# LLMVul Artifact Repository

This repository contains the processed vulnerability localization dataset and experiment artifacts used in our study on LLM-based vulnerability localization.

## Overview
The repository provides:
- A processed dataset derived from the original corpus used in our experiments.
- Function-level ground-truth labels for vulnerability localization (C/C++ and Java).
- Model configuration metadata for the LLMs used in the study.
- Scripts and artifacts for eight zero-shot experiments (Java and C).
- A human verification UI and double-review workflow for relevance analysis.

## Repository Layout
- `000_original_datasets/`
  - Processed dataset used in experiments (original source code and metadata).
- `001_ground_truth_datasets/`
  - Function-level ground-truth dataset for localization (C/C++ and Java).
- `002_model_infos/`
  - Model configuration summaries for all evaluated LLMs.
- `100_zero_shot_with_assumption_java/` to `103_zero_shot_without_assump_no_format_java/`
  - Java-focused zero-shot experiments (four configurations).
- `110_zero_shot_with_assumption_c/` to `113_zero_shot_without_assump_no_format_c/`
  - C-focused zero-shot experiments (four configurations).
- `llmvul.yml`
  - Conda environment used for scripts and analysis.

## Dataset Details
### 000_original_datasets
Processed dataset entries include (fields may vary slightly by language):
- `id`, `sub_id`, `code_id`
- `cve_id`, `cwe_id`
- `filename`
- `code`
- `is_vulnerable`
- `human_patch` (when available)

### 001_ground_truth_datasets
Function-level ground-truth data used for localization (C/C++ and Java). Fields include:
- `id`, `sub_id`, `code_id`, `function_id`
- `cve_id`, `cwe_id`
- `filename`
- `class_name`, `subclass_name`
- `function_name`, `function_body`
- `is_vulnerable`
- `human_patch`

### 002_model_infos
One file per model, containing model identifiers and configuration notes used in the experiments.

## Experiment Artifacts (100-103, 110-113)
Each experiment folder follows a consistent structure:
- `01_initial_src/` - Scripts used to run the initial LLM inference and data collection.
- `02_initial_results/` - Sample outputs only (full results not included).
- `03_relevance_analyze_llm_src/` - LLM-driven relevance analysis pipeline (e.g., Llama 3.3).
- `04_relevant_analysis_results/` - Intermediate relevance analysis outputs.
- `05_reponse_relevance_analysis_src/` - Human verification UI and workflow.
- `06_relevant_analysis_final_results/` - Final relevance-labeled outputs.

## Human Verification Workflow
The relevance analysis follows a staged review process:
1. An LLM performs the initial relevance analysis of vulnerability localization responses.
2. Human reviewers independently assess the same responses.
3. If the LLM and human decisions disagree, a second round of human review is triggered.
4. The final decision is made by the last human reviewer based on the LLM output and prior human review.

This double-checking reduces both model and human errors and produces the final relevance labels used in analysis.

## Notes on Scope
- Additional evaluation and hallucination analysis code is not included in this repository.
- Only sample LLM outputs are provided in `02_initial_results/`.

## Usage
The repository is provided primarily for inspection. If you need to rerun scripts locally, use the environment file:

```bash
conda env create -f llmvul.yml
```
