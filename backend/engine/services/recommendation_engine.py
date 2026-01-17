from decimal import Decimal
from typing import List

from django.db.models import F, Q, Value, DecimalField
from django.db.models.functions import Cast

from engine.models import (
    AIModel, UsageAnalysis, Recommendation, RecommendationType
)


class RecommendationEngine:
    """
    Generates model recommendations based on usage analysis.
    """

    # Minimum headroom multiplier for context window (1.2 = 20% headroom)
    CONTEXT_HEADROOM_MULTIPLIER = 1.2

    # Minimum cost savings to recommend (10%)
    MIN_COST_SAVINGS_PERCENT = 10

    # Confidence score weights
    WEIGHT_COST_SAVINGS = 0.5
    WEIGHT_CAPABILITY_MATCH = 0.3
    WEIGHT_CONTEXT_HEADROOM = 0.2

    def generate_recommendations(
        self,
        usage_analysis: UsageAnalysis,
        max_recommendations: int = 5
    ) -> List[Recommendation]:
        """
        Generate recommendations for a usage analysis record.

        Filters candidate models by:
        1. context_window >= max_tokens_used * headroom_multiplier
        2. supports_tools = True (if user requires tools)
        3. is_active = True
        4. Has pricing data
        5. Estimated cost < current cost
        """

        # Calculate required context window with headroom
        required_context = int(
            usage_analysis.max_total_tokens * self.CONTEXT_HEADROOM_MULTIPLIER
        )

        # Get current cost
        current_avg_cost = float(usage_analysis.avg_cost_per_request)
        if current_avg_cost <= 0:
            # Can't recommend if we don't know current cost
            return []

        avg_input = usage_analysis.avg_input_tokens
        avg_output = usage_analysis.avg_output_tokens

        # Build base queryset
        candidates = AIModel.objects.filter(
            is_active=True,
            pricing__isnull=False,
        ).select_related('pricing', 'provider')

        # Filter by context window
        if required_context > 0:
            candidates = candidates.filter(
                Q(context_window__gte=required_context) |
                Q(context_window__isnull=True)
            )

        # Filter by tool support if required
        if usage_analysis.requires_tools:
            candidates = candidates.filter(supports_tools=True)

        # Exclude the current model if resolved
        if usage_analysis.model_id:
            candidates = candidates.exclude(id=usage_analysis.model_id)

        # Annotate with estimated cost
        # Formula: (avg_input_tokens * input_price + avg_output_tokens * output_price) / 1_000_000
        # Use Decimal values and specify output_field to avoid type inference issues
        candidates = candidates.annotate(
            estimated_cost=(
                (Value(Decimal(str(avg_input)), output_field=DecimalField()) * F('pricing__request_token_price') +
                 Value(Decimal(str(avg_output)), output_field=DecimalField()) * F('pricing__response_token_price')) / Value(Decimal('1000000'), output_field=DecimalField())
            )
        )

        # Filter to cheaper options only (at least MIN_COST_SAVINGS_PERCENT savings)
        max_cost = Decimal(str(current_avg_cost * (1 - self.MIN_COST_SAVINGS_PERCENT / 100)))
        candidates = candidates.filter(estimated_cost__lt=max_cost)

        # Order by estimated cost (cheapest first)
        candidates = candidates.order_by('estimated_cost')

        # Limit results
        candidates = list(candidates[:max_recommendations * 2])

        # Deactivate old recommendations for this usage analysis
        Recommendation.objects.filter(
            usage_analysis=usage_analysis,
            is_active=True
        ).update(is_active=False)

        # Generate recommendation objects
        recommendations = []
        seen_providers = set()

        for candidate in candidates:
            if len(recommendations) >= max_recommendations:
                break

            # Calculate metrics
            estimated_cost = float(candidate.estimated_cost) if candidate.estimated_cost else 0

            cost_savings_pct = 0
            if current_avg_cost > 0:
                cost_savings_pct = ((current_avg_cost - estimated_cost) / current_avg_cost) * 100

            # Calculate context headroom
            context_headroom = 0
            if candidate.context_window and usage_analysis.max_total_tokens > 0:
                context_headroom = (
                    (candidate.context_window - usage_analysis.max_total_tokens)
                    / usage_analysis.max_total_tokens * 100
                )

            # Calculate capability match score
            capability_score = self._calculate_capability_score(
                candidate, usage_analysis
            )

            # Calculate confidence score
            confidence = self._calculate_confidence(
                cost_savings_pct=cost_savings_pct,
                capability_score=capability_score,
                context_headroom=context_headroom,
            )

            # Determine recommendation type
            rec_type = RecommendationType.CHEAPER
            if cost_savings_pct >= 50:
                rec_type = RecommendationType.CHEAPER
            elif capability_score > 100:
                rec_type = RecommendationType.CAPABLE

            # Estimate monthly savings
            monthly_requests = usage_analysis.total_requests
            monthly_savings = Decimal(str(
                (current_avg_cost - estimated_cost) * monthly_requests
            ))

            # Generate reasoning
            reasoning = self._generate_reasoning(
                candidate, usage_analysis, cost_savings_pct, context_headroom
            )

            # Create recommendation
            rec = Recommendation(
                application=usage_analysis.application,
                usage_analysis=usage_analysis,
                current_model_name=usage_analysis.raw_model_name,
                recommended_model=candidate,
                recommendation_type=rec_type,
                estimated_cost_savings_percent=cost_savings_pct,
                estimated_monthly_savings=monthly_savings,
                context_window_headroom=context_headroom,
                capability_match_score=capability_score,
                reasoning=reasoning,
                confidence_score=confidence,
            )
            recommendations.append(rec)
            seen_providers.add(candidate.provider_id)

        # Bulk create
        if recommendations:
            Recommendation.objects.bulk_create(recommendations)

        return recommendations

    def _calculate_capability_score(
        self,
        candidate: AIModel,
        usage: UsageAnalysis
    ) -> float:
        """
        Calculate how well candidate capabilities match user needs.
        100 = exact match, >100 = has extra features, <100 = missing features
        """
        score = 100.0

        # Check tool support
        if usage.requires_tools:
            if candidate.supports_tools:
                score += 0  # Required and present
            else:
                score -= 50  # Required but missing
        elif candidate.supports_tools:
            score += 5  # Bonus for having tools even if not required

        # Bonus for additional capabilities
        if candidate.supports_image_input:
            score += 5
        if candidate.has_reasoning:
            score += 10
        if candidate.supports_cache_control:
            score += 3

        return score

    def _calculate_confidence(
        self,
        cost_savings_pct: float,
        capability_score: float,
        context_headroom: float,
    ) -> float:
        """Calculate overall confidence score (0-1)."""

        # Normalize inputs to 0-1 scale
        cost_factor = min(cost_savings_pct / 50, 1.0)  # 50% savings = max
        capability_factor = min(capability_score / 100, 1.0)
        headroom_factor = min(context_headroom / 100, 1.0) if context_headroom > 0 else 0.5

        confidence = (
            self.WEIGHT_COST_SAVINGS * cost_factor +
            self.WEIGHT_CAPABILITY_MATCH * capability_factor +
            self.WEIGHT_CONTEXT_HEADROOM * headroom_factor
        )

        return round(confidence, 3)

    def _generate_reasoning(
        self,
        candidate: AIModel,
        usage: UsageAnalysis,
        cost_savings_pct: float,
        context_headroom: float
    ) -> str:
        """Generate human-readable reasoning for the recommendation."""
        reasons = []

        if cost_savings_pct >= 10:
            monthly_savings = float(usage.avg_cost_per_request) * usage.total_requests * (cost_savings_pct / 100)
            reasons.append(
                f"Save approximately {cost_savings_pct:.0f}% on costs "
                f"(~${monthly_savings:.4f}/month based on {usage.total_requests} requests)"
            )

        if context_headroom >= 50 and candidate.context_window:
            reasons.append(
                f"Context window of {candidate.context_window:,} tokens "
                f"provides {context_headroom:.0f}% headroom over your peak usage of {usage.max_total_tokens:,} tokens"
            )

        if candidate.supports_tools and usage.requires_tools:
            reasons.append("Supports tool/function calling as required by your usage")

        if candidate.has_reasoning:
            reasons.append("Includes advanced reasoning capabilities")

        if not reasons:
            reasons.append(f"Compatible alternative from {candidate.provider.name}")

        return ". ".join(reasons) + "."
