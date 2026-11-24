from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.schemas.application import Comment

_COMMENT_MIN_LENGTH = 5


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["approve", "reject", "return"]
    # validate_default: проверка ниже срабатывает и когда комментарий не прислан вовсе
    comment: Comment = Field(default=None, validate_default=True)

    @field_validator("comment")
    @classmethod
    def _required_for_reject_and_return(
        cls, comment: str | None, info: ValidationInfo
    ) -> str | None:
        # при отклонении и возврате заявитель должен увидеть причину
        if info.data.get("action") in ("reject", "return") and (
            comment is None or len(comment) < _COMMENT_MIN_LENGTH
        ):
            raise ValueError(f"Укажите причину — не меньше {_COMMENT_MIN_LENGTH} символов")
        return comment
