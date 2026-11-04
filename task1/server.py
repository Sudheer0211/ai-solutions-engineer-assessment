"""T1-003: public low-level SDK dispatch, with explicit validation."""

import json
import logging

from mcp import MCPError
from mcp.server import Server, ServerRequestContext
from mcp.types import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    PaginatedRequestParams,
    TextContent,
    Tool,
)
from pydantic import ValidationError

from task1.repository import BusinessError, MockRepository
from task1.schemas import GetCustomerArguments, RefundArguments
from task1.service import CustomerService

logger = logging.getLogger(__name__)
ARGUMENT_MODELS = {
    "get_customer_record": GetCustomerArguments,
    "trigger_refund": RefundArguments,
}


def tool_result(data: dict[str, str], *, is_error: bool = False) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(data, allow_nan=False))],
        structured_content=data,
        is_error=is_error,
    )


def create_server(repository: MockRepository | None = None) -> Server:
    """Each server owns fresh mock state unless a repository is injected."""
    service = CustomerService(repository if repository is not None else MockRepository())

    async def list_tools(
        ctx: ServerRequestContext, params: PaginatedRequestParams | None
    ) -> ListToolsResult:
        return ListToolsResult(
            tools=[
                Tool(
                    name=name,
                    description=description,
                    input_schema=ARGUMENT_MODELS[name].model_json_schema(),
                )
                for name, description in (
                    ("get_customer_record", "Look up a synthetic customer record."),
                    ("trigger_refund", "Record a mock refund and deduct the available balance."),
                )
            ]
        )

    async def call_tool(ctx: ServerRequestContext, params: CallToolRequestParams) -> CallToolResult:
        model = ARGUMENT_MODELS.get(params.name)
        if model is None:
            logger.warning("Unknown tool rejected")
            raise MCPError(code=INVALID_PARAMS, message="Unknown tool name")
        try:
            arguments = model.model_validate(params.arguments)
        except ValidationError:
            logger.warning("Validation failed tool=%s", params.name)
            raise MCPError(code=INVALID_PARAMS, message="Invalid tool arguments") from None
        logger.info("Tool execution tool=%s", params.name)
        try:
            if isinstance(arguments, GetCustomerArguments):
                return tool_result(service.get_customer_record(arguments))
            return tool_result(service.trigger_refund(arguments))
        except BusinessError as exc:
            logger.warning("Business operation failed tool=%s", params.name)
            return tool_result({"error": str(exc)}, is_error=True)
        except Exception:
            logger.error("Unexpected tool exception tool=%s", params.name)
            raise MCPError(code=INTERNAL_ERROR, message="Internal server error") from None

    return Server(
        "task1-customer-refund",
        version="0.1.0",
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )
