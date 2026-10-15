# EXTRACTION TASK

Convert table cells into a JSON-formatted list of entries. Each metric cell usually corresponds to one entry, populated with row-level metadata (shared across the row) and cell-level metadata (specific to that cell).

Do not create a separate entry for the number of parameters (treat it as metadata for the other entries).

## INPUT SPECIFICATION

You will receive a rendered table image. Extract entries based on the visual layout 
of cells, headers, and any captions or metadata visible in or near the table.

## WORKFLOW & TABLE STRUCTURE

A table contains column headers, row headers (leftmost), data cells, and optional additional info (captions, notes, metadata). To extract entries: (1) extract all interpretable metric cells, creating entries with available data and `null` for missing/unclear fields; (2) populate fields from row headers, column headers, and additional info; (3) identify and list all data quality issues, noting affected rows and fields.

Row headers are always the leftmost column of the table. Column headers are the topmost row. Treat merged cells in headers as applying to all subsumed rows/columns.

Fields can reside in three locations:

1. Additional info: Explicitly provided text, captions, or metadata
2. Row headers: Applies to all entries in that row
3. Column headers: Applies to a single column or column group


## ENTRY STRUCTURE

Each entry has the following fields:
{field_descriptions}


## FIELD ASSIGNMENT & SPECIAL CASES

| Scenario | Action |
|----------|--------|
| metric_name unavailable |	Assign `null` (always include field) |
| Column does not exist in the table or additional info | Completely omit field from entry (do not include it, not even as null) |
| Column exists in table but this specific cell is empty or unclear | Include field with value `null` |
| Cell unintelligible | Assign `null` + flag issue |
| Valid data present | Extract as-is |
| Confidence intervals (e.g., "0.85 ± 0.02") | Extract main value only; no flagging needed |
| Ranges (e.g., "0.75-0.90") | Assign `null`; flag issue |
| formatted numbers (e.g., "123.456k") | extract as integer |
| formatted numbers (e.g., "1.1E-3") | extract as float (in this case 0.0011) |
| percentages (either specified in value or column head; e.g., "0.3%" or "3.0E-1 %") | extract as float (in this case 0.003) |
| averages (e.g., "average", "avg.") | do not create an entry |
| multiple values (e.g., "0.82, 0.85") | create separate entries with same row-level metadata, different metric_value or evaluation_task; if meaning is not explicitly given, flag issue |
| joining two columns (parameters & metrics) | do not add parameters as a separate entry; instead, add to trained_parameters field for the respective metric values |
| parameter ratio given as percentage (%) | divide the values by 100 to derive the ratio |


## VISUAL AMBIGUITIES

| Scenario | Action |
|----------|--------|
| Merged cells (rows or columns) | Extract value once per logical group; flag if unclear which entry owns the value |
| Partial/obscured text | Assign `null` + flag issue with description of obscured content |
| Formatted emphasis (bold, color, shading) | Extract value normally; do not interpret formatting as semantic |
| Rotated or vertical text | Extract as-is; flag if text direction creates ambiguity |
| Superscript/subscript markers (e.g., ^1, ₂) | Extract main value; ignore notation unless critical to meaning |


## NORMALIZING METRIC NAMES

Use the following canonical versions of the metric names (replace alternative versions with the canonical name in the output):

| canonical | variants |
|-----------|----------|
| accuracy | acc, acc., acc, accuracy |
| matthews correlation coefficient | matthews, mcc |
| pearson correlation coefficient | pearson, pmcc, pcc |

If metric names are in column headers (e.g., 'sst-2 (acc.)'), extract 'acc.' and normalize to 'accuracy'.

## ISSUES TO FLAG

Flag issues including: missing critical fields, unintelligible or range data, unclear field locations, alternatives without explicit context, inconsistent data types, and missing additional info.

Issues should include table cell position (row index, column index) when possible. If multiple cells are affected, only include an example. Do not repeat the same issue multiple times. Do not specify all rows exhaustively.


## OUTPUT FORMAT

```json
{{
  "entries": [
    {{
      "method": "string or null",
      "model": "string or null",
      "evaluation_task": "string or null",
      "metric_name": "string",
      "metric_value": "number or null",
      "trained_parameters": "number or null",
      "average_rank": "number or null",
      "trained_parameter_ratio": "number or null",
      "finetuning_task": "string or null"
    }}
  ],
  "issues": [
    "string including position in the table",
    "potentially multiple entries for multiple issues"
  ]
}}
```

## EXAMPLE 1

### Table

| Method | Model | SST-2 | CoNLL03 |
|--------|-------|----------|----------|
| Fine-tuning | BERT | 0.91 | 0.88 
| Fine-tuning | BERT | - | 0.92 |
| Prompt-tuning | GPT-3.5 | 0.87 ± 0.03 | 0.84 |

### Additional Info
Task: Named Entity Recognition (NER) and Part-of-Speech Tagging (POS)

### Output
```json
{{
  "entries": [
    {{ "method": "Fine-tuning", "model": "BERT", "evaluation_task": "SST-2", "metric_value": 0.91, "metric_name": null }},
    {{ "method": "Fine-tuning", "model": "BERT", "evaluation_task": "CoNLL03", "metric_value": 0.88, "metric_name": null }},
    {{ "method": "Fine-tuning", "model": "BERT", "evaluation_task": "CoNLL03", "metric_value": 0.92, "metric_name": null }},
    {{ "method": "Prompt-tuning", "model": "GPT-3.5", "evaluation_task": "SST-2", "metric_value": 0.87, "metric_name": null }},
    {{ "method": "Prompt-tuning", "model": "GPT-3.5", "evaluation_task": "CoNLL03", "metric_value": 0.84, "metric_name": null }}
  ],
  "issues": [
    "Row 2, Column SST-2 (cell [2,3]): missing value; assigned null.",
    "Rank column not present; average_rank omitted.",
    "Metric names not specified."
  ]
}}
```

---

## EXAMPLE 2

## Table

| Method | Rank | #Params | SST-2 (Acc.) | CoNLL03 (F1) |
|--------|------|---------|--------------|--------------|
| LoRA | 16 | 0.21M | 0.91 | 0.88 
| AdaLoRA | 16 | 0.22M | 0.8 | 0.92 |
| EVA | 16 | 0.23M | 0.82 | 0.99 |

## Additional Info
Model: llama-7b, fine-tuned on train split of evaluation_task

## Output
```json
{{
  "entries": [
    {{ "method": "LoRA", "model": "llama-7b", "evaluation_task": "SST-2", "finetuning_task": "SST-2", "metric_name": "accuracy", "metric_value": 0.91, "trained_parameters": 21000000, "average_rank": 16}},
    {{ "method": "LoRA", "model": "llama-7b", "evaluation_task": "CoNLL03", "finetuning_task": "CoNLL03", "metric_name": "F1-score", "metric_value": 0.88, "trained_parameters": 21000000, "average_rank": 16 }},
    {{ "method": "AdaLoRA", "model": "llama-7b", "evaluation_task": "SST-2", "finetuning_task": "SST-2", "metric_name": "accuracy", "metric_value": 0.8, "trained_parameters": 22000000, "average_rank": 16 }},
    {{ "method": "AdaLoRA", "model": "llama-7b", "evaluation_task": "CoNLL03", "finetuning_task": "CoNLL03", "metric_name": "F1-score", "metric_value": 0.92, "trained_parameters": 22000000, "average_rank": 16 }},
    {{ "method": "EVA", "model": "llama-7b", "evaluation_task": "SST-2", "finetuning_task": "SST-2", "metric_name": "accuracy", "metric_value": 0.82, "trained_parameters": 23000000, "average_rank": 16 }},
    {{ "method": "EVA", "model": "llama-7b", "evaluation_task": "CoNLL03", "finetuning_task": "CoNLL03", "metric_name": "F1-score", "metric_value": 0.99, "trained_parameters": 23000000, "average_rank": 16 }}
  ],
  "issues": []
}}
```

---

# EXAMPLE 3


### Table
| Method | Model | Results |        |
|--------|-------|---------|--------|
|        |       | SST-2   | CoNLL  |
| LoRA   | BERT  | 0.91    | 0.88   |

### Output
```json
{{
  "entries": [
    {{ "method": "LoRA", "model": "BERT", "evaluation_task": "SST-2", "metric_value": 0.91, ... }},
    {{ "method": "LoRA", "model": "BERT", "evaluation_task": "CoNLL", "metric_value": 0.88, ... }}
  ],
  "issues": [
    "Row 1: column headers (Results) are merged; subheaders in row 2 clarify tasks."
  ]
}}
```

---

# INPUT

## Additional Info
{info}
