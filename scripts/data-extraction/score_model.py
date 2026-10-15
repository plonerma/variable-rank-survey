from pydantic import BaseModel, Field



class ResultEntryModel(BaseModel):
    method: str | None = Field(None, description="finetuning method used to adapt the model to the task (e.g., LoRA, AdaLoRA; remove references such as '[13]')")
    model: str | None = Field(None, description="backbone model adapted to the task (e.g., bert-base-cased, llama-2-7B)")
    evaluation_task: str | None = Field(None, description="task the model is evaluated on (e.g., SST-2, ConLL-2003; if only one task is given, it is the evaluation task)")
    metric_name: str | None = Field(None, description="metric being measured (e.g., Accuracy, F1-score, BLEU-score, etc.)")
    metric_value: float | None = Field(None, description="numeric value of the cell (extract as displayed; preserve decimal places shown in the table; do not round or invent precision)")
    trained_parameters: int | None = Field(None, gt=0, description="total trained/trainable parameters. Extract directly from a '#params' or similar column if present. If no such column exists, omit this field entirely. Do not calculate or derive)")
    average_rank: int | str | None = Field(None, description="average LoRA rank after training (often given as r)")
    trained_parameter_ratio: float | None = Field(None, gt=0.0, le=1.0, description="ratio of trained parameters to the total number of parameters in the model (omit if absent, do not derive)")
    finetuning_task: str | None = Field(None, description="task the model is finetuned on (e.g., SST-2, ConLL-2003; given only in some cases; may match evaluation_task)")

    @classmethod
    def fields_description_text(cls) -> str:
        return "\n".join(
            f"- {k}: {v.description}" for k, v in cls.model_fields.items()
        )


class ResultsModel(BaseModel):
    entries: list[ResultEntryModel] = Field(min_length=1)
    issues: list[str]


result_schema = ResultsModel.model_json_schema()
