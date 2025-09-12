"""Dependencies for template operations in the orchestrator."""

import uuid
from typing import Annotated

from fastapi import Body, Depends, Request

from orchestrator.exceptions import ItemNotFoundError
from orchestrator.v1.models import Template
from orchestrator.v1.templates.crud import get_template
from orchestrator.v1.templates.schemas import TemplateCreate

TemplateDep = Annotated[Template | None, Depends(get_template)]


def template_required(
    request: Request, template_id: uuid.UUID, template: TemplateDep
) -> Template:
    """Dependency to ensure the specified template exists.

    Args:
        request (Request): The current FastAPI request object.
        template_id (uuid.UUID): The UUID of the template to check.
        template (Template | None): The template instance if found, otherwise None.

    Raises:
        ItemNotFoundError: If the template does not exist.

    """
    if template is None:
        message = f"Template with id={template_id!s} does not exist"
        request.state.logger.error(message)
        raise ItemNotFoundError(message)
    return template


TemplateRequiredDep = Annotated[Template, Depends(template_required)]


def parse_template(template: Annotated[str, Body()]) -> TemplateCreate:
    """Depencency to encapsulate template into a pydantic schema.

    Args:
        template (str): TOSCA templates read from body.

    Returns:
        TemplateCreate: pydantic schema with the TOSCA template and derived attributes

    """
    return TemplateCreate(content=template)


TemplateCreateDep = Annotated[Template, Depends(parse_template)]
