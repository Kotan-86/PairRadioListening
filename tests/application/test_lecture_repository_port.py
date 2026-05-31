# 仕様: docs/spec/application.md#実装方針（ポート Outbound）
from application.ports.errors import PersistencePortError
from application.ports.mappers import to_persistence_failed


def test_to_persistence_failed_maps_port_error_to_application_error():
    port_error = PersistencePortError(operation="save", resource="lecture", reason="disk full")

    app_error = to_persistence_failed("start_lecture", port_error)

    assert app_error.use_case == "start_lecture"
    assert app_error.operation == "save"
    assert app_error.resource == "lecture"
