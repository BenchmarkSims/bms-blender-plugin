from collections import OrderedDict
from contextlib import contextmanager
from time import perf_counter


class ExportProfiler:
    """Collects stage-level export timings."""

    def __init__(self):
        self._durations = OrderedDict()

    @contextmanager
    def stage(self, stage_name):
        start_time = perf_counter()
        try:
            yield
        finally:
            self.add_duration(stage_name, perf_counter() - start_time)

    def add_duration(self, stage_name, duration_seconds):
        current_duration = self._durations.get(stage_name, 0.0)
        self._durations[stage_name] = current_duration + duration_seconds

    def has_records(self):
        return len(self._durations) > 0

    def format_summary(self):
        total_duration = sum(self._durations.values())
        lines = ["Export timing summary:"]
        for stage_name, duration_seconds in self._durations.items():
            percent = (duration_seconds / total_duration * 100) if total_duration else 0.0
            lines.append(f"  {stage_name}: {duration_seconds:.3f}s ({percent:.1f}%)")
        lines.append(f"  total tracked: {total_duration:.3f}s")
        return "\n".join(lines)
