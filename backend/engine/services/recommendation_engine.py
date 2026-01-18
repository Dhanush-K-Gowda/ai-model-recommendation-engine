from decimal import Decimal
from typing import List

from django.db import connection
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

    # Minimum cost savings to recommend (increased from 5% to 10%)
    MIN_COST_SAVINGS_PERCENT = 1

    # Minimum context headroom percentage (models must have at least this much headroom)
    MIN_CONTEXT_HEADROOM_PERCENT = 1

    # Minimum confidence score to include a recommendation (0-100)
    MIN_CONFIDENCE_SCORE = 0

    # Maximum number of recommendations to generate
    DEFAULT_MAX_RECOMMENDATIONS = 5

    # Maximum number of recommendations per provider
    MAX_RECOMMENDATIONS_PER_PROVIDER = 2

    # Confidence score weights
    WEIGHT_COST_SAVINGS = 0.5
    WEIGHT_CAPABILITY_MATCH = 0.3
    WEIGHT_CONTEXT_HEADROOM = 0.2

    def generate_recommendations(
        self,
        usage_analysis: UsageAnalysis,
        max_recommendations: int = None
    ) -> List[Recommendation]:
        """
        Generate recommendations for a usage analysis record.

        Filters candidate models by:
        1. Category matches application category (or 'general' category)
        2. context_window >= max_tokens_used * headroom_multiplier
        3. supports_tools = True (if user requires tools)
        4. is_active = True
        5. Has pricing data
        6. Estimated cost < current cost (with minimum savings threshold)
        7. Minimum context headroom
        8. Minimum confidence score
        """

        # Use default if not specified
        if max_recommendations is None:
            max_recommendations = self.DEFAULT_MAX_RECOMMENDATIONS

        # Get application categories (now a list)
        app_categories = usage_analysis.application.categories or ['general']
        if not app_categories:
            app_categories = ['general']  # Default fallback

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
            # Require context_window to be set (no null values)
            context_window__isnull=False,
        ).select_related('pricing', 'provider')

        # Filter by category - models must have at least one matching category
        # from application's categories, or have 'general' category (which works for all)
        # Also include models with null categories (for backward compatibility)
        
        # SQLite doesn't support __contains on JSONField, so we'll filter in Python later
        # For other databases, use database-level filtering
        if connection.vendor != 'sqlite':
            category_conditions = Q(categories__isnull=True)  # Include models without categories for now
            
            # Check if model has 'general' category (works for all applications)
            category_conditions |= Q(categories__contains=['general'])
            
            # Check if model has any of the application's categories
            for app_category in app_categories:
                if app_category != 'general':  # Skip 'general' as we already checked it
                    category_conditions |= Q(categories__contains=[app_category])
            
            candidates = candidates.filter(category_conditions)

        # Filter by context window - require models to have sufficient context
        if required_context > 0:
            candidates = candidates.filter(
                context_window__gte=required_context
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

        # For SQLite, filter by category in Python after getting candidates
        # For other databases, category filtering was already done above
        if connection.vendor == 'sqlite':
            # Get candidates first (more than needed for filtering)
            candidate_list = list(candidates[:max_recommendations * 10])
            
            # Filter by category in Python
            filtered_candidates = []
            for candidate in candidate_list:
                model_categories = candidate.categories or []
                
                # Include if no categories (backward compatibility)
                if not model_categories:
                    filtered_candidates.append(candidate)
                    continue
                
                # Include if has 'general' category
                if 'general' in model_categories:
                    filtered_candidates.append(candidate)
                    continue
                
                # Include if has any matching category from application
                if any(cat in model_categories for cat in app_categories if cat != 'general'):
                    filtered_candidates.append(candidate)
                    continue
            
            candidates = filtered_candidates[:max_recommendations * 3]
        else:
            # Limit results before processing
            candidates = list(candidates[:max_recommendations * 3])  # Get more candidates for filtering

        # Deactivate old recommendations for this usage analysis
        Recommendation.objects.filter(
            usage_analysis=usage_analysis,
            is_active=True
        ).update(is_active=False)

        # Generate recommendation objects
        recommendations = []
        seen_providers = {}
        provider_counts = {}

        for candidate in candidates:
            # Stop if we've reached max recommendations
            if len(recommendations) >= max_recommendations:
                break

            # Limit recommendations per provider
            provider_id = candidate.provider_id
            if provider_id not in provider_counts:
                provider_counts[provider_id] = 0
            
            if provider_counts[provider_id] >= self.MAX_RECOMMENDATIONS_PER_PROVIDER:
                continue

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

            # Filter by minimum context headroom
            if context_headroom < self.MIN_CONTEXT_HEADROOM_PERCENT:
                continue

            # Calculate capability match score
            capability_score = 100  # Base score
            
            # Boost score for matching capabilities
            if usage_analysis.requires_tools and candidate.supports_tools:
                capability_score += 20
            
            if candidate.has_reasoning:
                capability_score += 10

            # Calculate confidence score using weights
            # Normalize cost savings (0-100 scale, assuming max 50% savings is excellent)
            cost_savings_normalized = min(cost_savings_pct / 50.0 * 100, 100)
            
            # Normalize context headroom (0-100 scale, assuming 100%+ headroom is excellent)
            context_headroom_normalized = min(context_headroom / 100.0 * 100, 100)
            
            # Capability score is already 0-100+
            capability_normalized = min(capability_score, 100)
            
            confidence = (
                cost_savings_normalized * self.WEIGHT_COST_SAVINGS +
                capability_normalized * self.WEIGHT_CAPABILITY_MATCH +
                context_headroom_normalized * self.WEIGHT_CONTEXT_HEADROOM
            )

            # Filter by minimum confidence score
            if confidence < self.MIN_CONFIDENCE_SCORE:
                continue

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
            seen_providers[provider_id] = candidate.provider
            provider_counts[provider_id] += 1

        # Sort by confidence score before bulk create
        recommendations.sort(key=lambda r: r.confidence_score, reverse=True)
        
        # Take only top N after sorting
        recommendations = recommendations[:max_recommendations]

        # Bulk create
        if recommendations:
            Recommendation.objects.bulk_create(recommendations)

        return recommendations

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
