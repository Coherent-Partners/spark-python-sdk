from __future__ import annotations

from typing import Any, Dict, Optional

__all__ = ['omit_none', 'McpToolsMixin']


def omit_none(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Drop keys whose values are None so MCP tools receive only set fields."""
    return {key: value for key, value in arguments.items() if value is not None}


class McpToolsMixin:
    """Typed helpers that map 1:1 to Coherent MCP tool names."""

    async def execute_v3(
        self,
        *,
        folder: str,
        service: str,
        version: Optional[str] = None,
        version_id: Optional[str] = None,
        request_payload: Optional[Dict[str, Any]] = None,
        call_purpose: Optional[str] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
        service_category: Optional[str] = None,
        transaction_date: Optional[str] = None,
    ) -> Any:
        return await self.call_tool(  # type: ignore[attr-defined]
            'spark_execute_v3',
            omit_none(
                {
                    'folder': folder,
                    'service': service,
                    'version': version,
                    'version_id': version_id,
                    'requestPayload': request_payload,
                    'call_purpose': call_purpose,
                    'source_system': source_system,
                    'correlation_id': correlation_id,
                    'service_category': service_category,
                    'transaction_date': transaction_date,
                }
            ),
        )

    async def service_info(
        self,
        *,
        folder: str,
        service: str,
        version: Optional[str] = None,
    ) -> Any:
        return await self.call_tool(  # type: ignore[attr-defined]
            'spark_service_info',
            omit_none({'folder': folder, 'service': service, 'version': version}),
        )

    async def generate_snippet(
        self,
        *,
        folder: str,
        service: str,
        version: Optional[str] = None,
        language_code: Optional[str] = None,
        language_variant: Optional[str] = None,
    ) -> Any:
        return await self.call_tool(  # type: ignore[attr-defined]
            'spark_generate_snippet',
            omit_none(
                {
                    'folder': folder,
                    'service': service,
                    'version': version,
                    'language_code': language_code,
                    'language_variant': language_variant,
                }
            ),
        )

    async def compare_service_versions(
        self,
        *,
        folder: str,
        service: str,
        version_1: Optional[str] = None,
        version_2: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> Any:
        return await self.call_tool(  # type: ignore[attr-defined]
            'spark_compare_service_versions',
            omit_none(
                {
                    'folder': folder,
                    'service': service,
                    'version_1': version_1,
                    'version_2': version_2,
                    'job_id': job_id,
                }
            ),
        )

    async def download_api_history(
        self,
        *,
        folder: str,
        service: str,
        version: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        call_ids: Optional[Any] = None,
        call_purpose: Optional[str] = None,
        username: Optional[str] = None,
        has_warnings: Optional[bool] = None,
        has_errors: Optional[bool] = None,
        include_inputs: Optional[bool] = None,
        include_outputs: Optional[bool] = None,
        requested_outputs: Optional[Any] = None,
        heading_order: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> Any:
        return await self.call_tool(  # type: ignore[attr-defined]
            'spark_download_api_history',
            omit_none(
                {
                    'folder': folder,
                    'service': service,
                    'version': version,
                    'start_date': start_date,
                    'end_date': end_date,
                    'call_ids': call_ids,
                    'call_purpose': call_purpose,
                    'username': username,
                    'has_warnings': has_warnings,
                    'has_errors': has_errors,
                    'include_inputs': include_inputs,
                    'include_outputs': include_outputs,
                    'requested_outputs': requested_outputs,
                    'heading_order': heading_order,
                    'job_id': job_id,
                }
            ),
        )

    async def download_testbed_template(self, *, folder: str, service: str) -> Any:
        return await self.call_tool(  # type: ignore[attr-defined]
            'spark_download_testbed_template',
            {'folder': folder, 'service': service},
        )

    async def download_testbed_result(
        self,
        *,
        folder: str,
        service: str,
        testbed: str,
        testbed_result: str,
    ) -> Any:
        return await self.call_tool(  # type: ignore[attr-defined]
            'spark_download_testbed_result',
            {
                'folder': folder,
                'service': service,
                'testbed': testbed,
                'testbed_result': testbed_result,
            },
        )

    async def list_testbeds(self, *, folder: str, service: str, testbed: Optional[str] = None) -> Any:
        return await self.call_tool(  # type: ignore[attr-defined]
            'spark_list_testbeds',
            omit_none({'folder': folder, 'service': service, 'testbed': testbed}),
        )

    async def list_testbed_results(
        self,
        *,
        folder: str,
        service: str,
        testbed: str,
        testbed_result_name: Optional[str] = None,
    ) -> Any:
        return await self.call_tool(  # type: ignore[attr-defined]
            'spark_list_testbed_results',
            omit_none(
                {
                    'folder': folder,
                    'service': service,
                    'testbed': testbed,
                    'testbed_result_name': testbed_result_name,
                }
            ),
        )

    async def run_testbed(
        self,
        *,
        folder: str,
        service: str,
        testbed: str,
        revision: Optional[str] = None,
        version_id: Optional[str] = None,
        service_category: Optional[str] = None,
        testbed_result: Optional[str] = None,
        testbed_result_description: Optional[str] = None,
        testbed_list_max_pages: Optional[int] = None,
    ) -> Any:
        return await self.call_tool(  # type: ignore[attr-defined]
            'spark_run_testbed',
            omit_none(
                {
                    'folder': folder,
                    'service': service,
                    'testbed': testbed,
                    'revision': revision,
                    'version_id': version_id,
                    'service_category': service_category,
                    'testbed_result': testbed_result,
                    'testbed_result_description': testbed_result_description,
                    'testbed_list_max_pages': testbed_list_max_pages,
                }
            ),
        )

    async def run_status_testbed(
        self,
        *,
        run_id: str,
        testbed: str,
        wait_for_complete: Optional[bool] = None,
        poll_interval_seconds: Optional[float] = None,
        max_iterations: Optional[int] = None,
        folder: Optional[str] = None,
        service: Optional[str] = None,
        revision: Optional[str] = None,
        version_id: Optional[str] = None,
        service_category: Optional[str] = None,
        testbed_result: Optional[str] = None,
        testbed_result_description: Optional[str] = None,
        testbed_list_max_pages: Optional[int] = None,
    ) -> Any:
        return await self.call_tool(  # type: ignore[attr-defined]
            'spark_run_status_testbed',
            omit_none(
                {
                    'run_id': run_id,
                    'testbed': testbed,
                    'wait_for_complete': wait_for_complete,
                    'poll_interval_seconds': poll_interval_seconds,
                    'max_iterations': max_iterations,
                    'folder': folder,
                    'service': service,
                    'revision': revision,
                    'version_id': version_id,
                    'service_category': service_category,
                    'testbed_result': testbed_result,
                    'testbed_result_description': testbed_result_description,
                    'testbed_list_max_pages': testbed_list_max_pages,
                }
            ),
        )

    async def compare_testbed_results(
        self,
        *,
        folder: str,
        service: str,
        testbed: str,
        testbed_result_1: str,
        testbed_result_2: str,
    ) -> Any:
        return await self.call_tool(  # type: ignore[attr-defined]
            'spark_compare_testbed_results',
            {
                'folder': folder,
                'service': service,
                'testbed': testbed,
                'testbed_result_1': testbed_result_1,
                'testbed_result_2': testbed_result_2,
            },
        )
