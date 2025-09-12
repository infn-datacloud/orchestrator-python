"""Dependencies for template operations in the federation manager."""

import uuid
from typing import Annotated

from fastapi import Body, Depends, HTTPException, Request, status

from orchestrator.v1.models import Template
from orchestrator.v1.templates.crud import get_template
from orchestrator.v1.templates.schemas import TemplateCreate

TemplateDep = Annotated[Template | None, Depends(get_template)]


def template_required(
    request: Request, template_id: uuid.UUID, template: TemplateDep
) -> Template:
    """Dependency to ensure the specified template exists.

    Raises an HTTP 404 error if the template with the given template_id does not
    exist.

    Args:
        request: The current FastAPI request object.
        template_id: The UUID of the template to check.
        template: The Template instance if found, otherwise None.

    Raises:
        HTTPException: If the template does not exist.

    """
    if template is None:
        message = f"Template with ID '{template_id!s}' does not exist"
        request.state.logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
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
