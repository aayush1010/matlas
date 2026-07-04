from matlas.eval.harness import BenchmarkResult
from matlas.eval.report import render_report


def test_render_report_does_not_raise():
    result = BenchmarkResult(n=2, merchant_accuracy=0.5, category_accuracy=1.0, mean_tool_calls=1.5)
    render_report(result)
