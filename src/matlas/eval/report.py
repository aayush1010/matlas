from rich.console import Console
from rich.table import Table

from matlas.eval.harness import BenchmarkResult


def render_report(result: BenchmarkResult, title: str = "matlas benchmark") -> None:
    table = Table(title=title)
    table.add_column("metric")
    table.add_column("value")
    table.add_row("n", str(result.n))
    table.add_row("merchant accuracy", f"{result.merchant_accuracy:.1%}")
    table.add_row("category accuracy", f"{result.category_accuracy:.1%}")
    if result.mean_tool_calls is not None:
        table.add_row("mean tool calls/txn", f"{result.mean_tool_calls:.2f}")
    Console().print(table)
