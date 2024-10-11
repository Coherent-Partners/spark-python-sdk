from typing import Any, BinaryIO, Dict, List, Optional, Union

from cspark.sdk import ApiResource, Uri, UriParams
from cspark.sdk import Services as SdkServices

__all__ = ['Services']


class Services(ApiResource):
    def upload(self, file: BinaryIO, file_name: Optional[str] = None):
        url = Uri.of(base_url=self.config.base_url.value, endpoint='upload')
        return self.request(url, method='POST', files={'file': (file_name or 'package.zip', file)})

    def execute(
        self,
        uri: Union[str, UriParams],
        *,
        inputs: Union[None, str, Dict[str, Any], List[Any]] = None,
        encoding: Optional[str] = None,
        response_format: Optional[str] = None,
        # Metadata for calculations
        active_since: Optional[str] = None,
        source_system: Optional[str] = None,
        correlation_id: Optional[str] = None,
        call_purpose: Optional[str] = None,
        compiler_type: Optional[str] = None,
        subservices: Union[None, str, List[str]] = None,
        # Available only in v3
        debug_solve: Optional[bool] = None,
        echo_inputs: Optional[bool] = False,
        tables_as_array: Union[None, str, List[str]] = None,
        selected_outputs: Union[None, str, List[str]] = None,
        outputs_filter: Optional[str] = None,
    ):
        with SdkServices(self.config) as services:
            return services.execute(
                uri,
                inputs=inputs,
                response_format=response_format,
                encoding=encoding,
                subservices=subservices,
                active_since=active_since,
                source_system=source_system,
                correlation_id=correlation_id,
                call_purpose=call_purpose,
                compiler_type=compiler_type,
                debug_solve=debug_solve,
                echo_inputs=echo_inputs,
                tables_as_array=tables_as_array,
                selected_outputs=selected_outputs,
                outputs_filter=outputs_filter,
            )
