# 仕様: docs/spec/interface.md#5.1-6 / §8.3-7
import ast
from pathlib import Path

APPLICATION_ROOT = Path(__file__).resolve().parents[2] / "application"


def _collect_imports(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports


def test_application_does_not_import_interface_adapters():
    offenders: list[str] = []
    for path in APPLICATION_ROOT.rglob("*.py"):
        if path.name == "__init__.py" and path.read_text(encoding="utf-8").strip() == "":
            continue
        if "interface_adapters" in _collect_imports(path):
            offenders.append(str(path.relative_to(APPLICATION_ROOT.parent)))

    assert offenders == []
