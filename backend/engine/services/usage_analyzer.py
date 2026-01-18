from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

from django.db.models import Max, Avg, Count, Sum, Q
from django.utils import timezone

from engine.models import Application, LLMTrace, UsageAnalysis
from engine.services.model_resolver import ModelResolver


class UsageAnalyzer:
    """
    Analyzes application trace data to compute usage patterns.
    """

    def __init__(self, analysis_period_days: int = 30):
        self.analysis_period_days = analysis_period_days

    def analyze_application(
        self,
        application: Application,
        end_date: datetime = None
    ) -> List[UsageAnalysis]:
        """
        Analyze all model usage for an application over the analysis period.
        Creates/updates UsageAnalysis records.
        """
        if end_date is None:
            end_date = timezone.now()
        start_date = end_date - timedelta(days=self.analysis_period_days)

        # Get all traces for application in period
        traces = LLMTrace.objects.filter(
            application=application,
            traced_at__gte=start_date,
            traced_at__lte=end_date
        )

        if not traces.exists():
            return []

        # Group by raw_model_name
        model_groups = traces.values('raw_model_name', 'model_id').annotate(
            total_requests=Count('id'),
            successful_requests=Count('id', filter=Q(status='success')),
            max_input_tokens=Max('input_token_count'),
            max_output_tokens=Max('output_token_count'),
            max_total_tokens=Max('total_token_count'),
            avg_input_tokens=Avg('input_token_count'),
            avg_output_tokens=Avg('output_token_count'),
            total_cost=Sum('total_cost'),
            avg_latency=Avg('estimated_latency_sec'),
            tool_used_count=Count('id', filter=Q(tool_used=True)),
        )

        analyses = []
        for group in model_groups:
            raw_model_name = group['raw_model_name']

            # Calculate tool usage percentage
            tool_pct = 0
            if group['total_requests'] > 0:
                tool_pct = group['tool_used_count'] / group['total_requests'] * 100

            # Calculate avg cost per request
            avg_cost = Decimal('0')
            if group['total_requests'] > 0 and group['total_cost']:
                avg_cost = group['total_cost'] / group['total_requests']

            # Calculate category distribution
            category_dist = self._calculate_category_distribution(
                traces.filter(raw_model_name=raw_model_name)
            )

            # Create or update analysis
            analysis, _ = UsageAnalysis.objects.update_or_create(
                application=application,
                raw_model_name=raw_model_name,
                analysis_period_start=start_date,
                defaults={
                    'model_id': group['model_id'],
                    'analysis_period_end': end_date,
                    'total_requests': group['total_requests'],
                    'successful_requests': group['successful_requests'],
                    'max_input_tokens': group['max_input_tokens'] or 0,
                    'max_output_tokens': group['max_output_tokens'] or 0,
                    'max_total_tokens': group['max_total_tokens'] or 0,
                    'avg_input_tokens': group['avg_input_tokens'] or 0,
                    'avg_output_tokens': group['avg_output_tokens'] or 0,
                    'total_cost': group['total_cost'] or Decimal('0'),
                    'avg_cost_per_request': avg_cost,
                    'avg_latency_sec': group['avg_latency'],
                    'tool_usage_percentage': tool_pct,
                    'requires_tools': tool_pct > 10,  # >10% usage = requires tools
                    'category_distribution': category_dist,
                }
            )
            analyses.append(analysis)

        return analyses

    def _calculate_category_distribution(self, traces) -> dict:
        """Calculate percentage distribution across categories."""
        total = traces.count()
        if total == 0:
            return {}

        distribution = traces.exclude(category='').values('category').annotate(
            count=Count('id')
        )

        return {
            item['category']: round(item['count'] / total * 100, 1)
            for item in distribution
            if item['category']
        }

    def analyze_all_applications(self) -> int:
        """
        Run analysis for all applications with recent traces.
        Returns count of applications analyzed.
        """
        cutoff = timezone.now() - timedelta(days=self.analysis_period_days)

        applications_with_traces = Application.objects.filter(
            traces__traced_at__gte=cutoff
        ).distinct()

        count = 0
        for app in applications_with_traces:
            self.analyze_application(app)
            count += 1

        return count
