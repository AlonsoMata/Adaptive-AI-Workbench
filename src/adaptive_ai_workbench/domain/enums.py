from enum import Enum


class ActionKind(str, Enum):
    prompt_transform = "prompt_transform"
    text_rewrite = "text_rewrite"
    summarization = "summarization"
    translation = "translation"
    extraction = "extraction"
    template_fill = "template_fill"
    code_review = "code_review"
    code_refactor_prompt = "code_refactor_prompt"
    cv_improvement = "cv_improvement"


class InputMode(str, Enum):
    single_text = "single_text"
    text_with_instruction = "text_with_instruction"
    structured_fields = "structured_fields"


class PackSource(str, Enum):
    template = "template"
    generated = "generated"
