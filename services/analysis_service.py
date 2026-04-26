from collections import defaultdict

from schemas.analysis_schema import AnalysisRequest, AnalysisResponse


class AnalysisService:
    def analyze(self, payload: AnalysisRequest) -> AnalysisResponse:
        tasks = payload.tasks
        if not tasks:
            return AnalysisResponse(
                average_time_minutes=0.0,
                slowest_tasks=[],
                overloaded_areas=[],
            )

        average_time = sum(task.duration_minutes for task in tasks) / len(tasks)
        slowest_threshold = max(task.duration_minutes for task in tasks)
        slowest_tasks = [task for task in tasks if task.duration_minutes == slowest_threshold]

        area_totals: dict[str, float] = defaultdict(float)
        for task in tasks:
            area_totals[task.area] += task.duration_minutes

        overloaded_areas = sorted(
            [{"area": area, "total_minutes": total} for area, total in area_totals.items()],
            key=lambda item: item["total_minutes"],
            reverse=True,
        )[:3]

        return AnalysisResponse(
            average_time_minutes=round(average_time, 2),
            slowest_tasks=slowest_tasks,
            overloaded_areas=overloaded_areas,
        )
