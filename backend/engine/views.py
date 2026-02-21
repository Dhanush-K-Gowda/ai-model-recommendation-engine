import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Avg, Count, F
from django.db import connection
from django.utils import timezone
from datetime import timedelta

from engine.models import (
    Application,
    LLMTrace,
    AIModel,
    UsageAnalysis,
    Recommendation,
    Provider,
)
from engine.serializers import TraceIngestionSerializer, TraceBulkIngestionSerializer
from engine.services.recommendation_engine import RecommendationEngine
from engine.services.usage_analyzer import UsageAnalyzer


def health_check(request):
    """Health check endpoint."""
    return JsonResponse(
        {
            "status": "success",
            "message": "API is healthy",
            "timestamp": timezone.now().isoformat(),
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def ingest_trace(request):
    """Ingest a single LLM trace."""
    try:
        data = json.loads(request.body)
        serializer = TraceIngestionSerializer(data=data)

        if serializer.is_valid():
            trace = serializer.save()
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Trace ingested successfully",
                    "data": {
                        "id": trace.id,
                        "external_id": trace.external_id,
                        "application_id": trace.application.application_id,
                        "model_name": trace.raw_model_name,
                        "traced_at": trace.traced_at.isoformat(),
                    },
                },
                status=201,
            )
        else:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Validation failed",
                    "errors": serializer.errors,
                },
                status=400,
            )
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def ingest_traces_bulk(request):
    """Ingest multiple LLM traces at once."""
    try:
        data = json.loads(request.body)
        serializer = TraceBulkIngestionSerializer(data=data)

        if serializer.is_valid():
            traces = serializer.save()
            return JsonResponse(
                {
                    "status": "success",
                    "message": f"{len(traces)} traces ingested successfully",
                    "data": {
                        "count": len(traces),
                        "traces": [
                            {
                                "id": trace.id,
                                "external_id": trace.external_id,
                                "application_id": trace.application.application_id,
                            }
                            for trace in traces
                        ],
                    },
                },
                status=201,
            )
        else:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Validation failed",
                    "errors": serializer.errors,
                },
                status=400,
            )
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_http_methods(["GET"])
def applications_list(request):
    """Get list of all applications with aggregated stats."""
    try:
        applications = Application.objects.all().prefetch_related("traces")

        # Get most recent usage analysis for each application using subquery
        app_ids = [app.application_id for app in applications]

        # Get recent analyses (most recent per app)
        recent_analyses = {}
        if app_ids:
            analyses = (
                UsageAnalysis.objects.filter(application__application_id__in=app_ids)
                .select_related("application", "model")
                .order_by("application_id", "-analysis_period_end")
            )

            for analysis in analyses:
                app_id = analysis.application.application_id
                if app_id not in recent_analyses:
                    recent_analyses[app_id] = analysis

        apps_data = []
        for app in applications:
            # Get aggregated stats from traces using DB aggregation
            traces = app.traces.all()
            total_requests = traces.count()
            agg = traces.aggregate(
                total_cost=Sum("total_cost"), total_tokens=Sum("total_token_count")
            )
            total_cost = float(agg["total_cost"] or 0)
            total_tokens = agg["total_tokens"] or 0

            # Get most recent model usage
            latest_trace = traces.order_by("-traced_at").first()
            model_name = latest_trace.raw_model_name if latest_trace else "Unknown"

            # Get usage analysis if available
            analysis = recent_analyses.get(app.application_id)
            usage = None
            if analysis:
                usage = {
                    "model_name": analysis.raw_model_name,
                    "total_requests": analysis.total_requests,
                    "avg_cost_per_request": float(analysis.avg_cost_per_request),
                    "max_total_tokens": analysis.max_total_tokens,
                    "avg_latency_sec": float(analysis.avg_latency_sec)
                    if analysis.avg_latency_sec
                    else None,
                }

            apps_data.append(
                {
                    "id": app.id,
                    "application_id": app.application_id,
                    "name": app.name or app.application_id,
                    "model": model_name,
                    "category": app.categories[0] if app.categories else "general",
                    "usage": usage,
                    "cost": f"${total_cost:.2f}",
                    "total_requests": total_requests,
                    "total_cost": float(total_cost),
                    "total_tokens": total_tokens,
                    "categories": app.categories or [],
                    "is_active": app.is_active,
                }
            )

        return JsonResponse(
            {
                "status": "success",
                "data": {"applications": apps_data, "count": len(apps_data)},
            }
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_http_methods(["GET"])
def application_detail(request, application_id):
    """Get detailed information about a specific application."""
    try:
        app = Application.objects.get(application_id=application_id)

        # Get aggregated stats using DB aggregation
        traces = app.traces.all()
        total_requests = traces.count()
        successful_requests = traces.filter(status="success").count()
        agg = traces.aggregate(
            total_cost=Sum("total_cost"), total_tokens=Sum("total_token_count")
        )
        total_cost = float(agg["total_cost"] or 0)
        total_tokens = agg["total_tokens"] or 0
        avg_cost = total_cost / total_requests if total_requests > 0 else 0
        avg_latency = traces.aggregate(avg=Avg("estimated_latency_sec"))["avg"]

        # Get most recent usage analysis
        usage_analysis = None
        latest_analysis = (
            UsageAnalysis.objects.filter(application=app)
            .order_by("-analysis_period_end")
            .first()
        )

        if latest_analysis:
            usage_analysis = {
                "model_name": latest_analysis.raw_model_name,
                "total_requests": latest_analysis.total_requests,
                "avg_cost_per_request": float(latest_analysis.avg_cost_per_request),
                "max_total_tokens": latest_analysis.max_total_tokens,
                "avg_latency_sec": float(latest_analysis.avg_latency_sec)
                if latest_analysis.avg_latency_sec
                else None,
            }

        # Get recommendations
        recommendations = []
        for rec in (
            Recommendation.objects.filter(
                application=app, is_active=True, is_dismissed=False
            )
            .select_related("recommended_model", "recommended_model__provider")
            .order_by("-confidence_score")[:10]
        ):
            recommendations.append(
                {
                    "id": rec.id,
                    "application_id": app.application_id,
                    "application_name": app.name,
                    "current_model": rec.current_model_name,
                    "recommended_model": rec.recommended_model.name
                    if rec.recommended_model
                    else None,
                    "provider": rec.recommended_model.provider.name
                    if rec.recommended_model
                    else None,
                    "recommendation_type": rec.recommendation_type,
                    "confidence_score": float(rec.confidence_score),
                    "cost_savings_percent": float(rec.estimated_cost_savings_percent),
                    "monthly_savings": float(rec.estimated_monthly_savings),
                    "reasoning": rec.reasoning,
                    "test_status": rec.test_status,
                    "quality_overall_score": float(rec.quality_overall_score)
                    if rec.quality_overall_score
                    else None,
                    "features": rec.recommended_model.categories
                    if rec.recommended_model and rec.recommended_model.categories
                    else [],
                }
            )

        return JsonResponse(
            {
                "status": "success",
                "data": {
                    "id": app.id,
                    "application_id": app.application_id,
                    "name": app.name or app.application_id,
                    "categories": app.categories or [],
                    "assigned_model": app.assigned_model
                    if hasattr(app, "assigned_model")
                    else None,
                    "is_active": app.is_active,
                    "stats": {
                        "total_requests": total_requests,
                        "successful_requests": successful_requests,
                        "total_cost": float(total_cost),
                        "avg_cost": float(avg_cost),
                        "total_tokens": total_tokens,
                        "avg_latency_sec": float(avg_latency) if avg_latency else None,
                    },
                    "usage_analysis": usage_analysis,
                    "recommendations": recommendations,
                },
            }
        )
    except Application.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Application not found"}, status=404
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def recommendations_list(request):
    """Get recommendations or generate new ones based on criteria."""
    if request.method == "GET":
        # Get existing recommendations
        application_id = request.GET.get("application_id")

        try:
            if application_id:
                app = Application.objects.get(application_id=application_id)
                recommendations = (
                    Recommendation.objects.filter(
                        application=app, is_active=True, is_dismissed=False
                    )
                    .select_related(
                        "application",
                        "recommended_model",
                        "recommended_model__provider",
                    )
                    .order_by("-confidence_score")
                )
            else:
                recommendations = (
                    Recommendation.objects.filter(is_active=True, is_dismissed=False)
                    .select_related(
                        "recommended_model",
                        "recommended_model__provider",
                        "application",
                    )
                    .order_by("-confidence_score")
                )

            recs_data = []
            for rec in recommendations[:20]:  # Limit to 20
                recs_data.append(
                    {
                        "id": rec.id,
                        "application_id": rec.application.application_id,
                        "application_name": rec.application.name,
                        "current_model": rec.current_model_name,
                        "recommended_model": rec.recommended_model.name
                        if rec.recommended_model
                        else None,
                        "provider": rec.recommended_model.provider.name
                        if rec.recommended_model
                        else None,
                        "recommendation_type": rec.recommendation_type,
                        "confidence_score": float(rec.confidence_score),
                        "cost_savings_percent": float(
                            rec.estimated_cost_savings_percent
                        ),
                        "monthly_savings": float(rec.estimated_monthly_savings),
                        "reasoning": rec.reasoning,
                        "test_status": rec.test_status,
                        "quality_overall_score": float(rec.quality_overall_score)
                        if rec.quality_overall_score
                        else None,
                        "features": rec.recommended_model.categories
                        if rec.recommended_model and rec.recommended_model.categories
                        else [],
                    }
                )

            return JsonResponse(
                {
                    "status": "success",
                    "data": {"recommendations": recs_data, "count": len(recs_data)},
                }
            )
        except Application.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Application not found"}, status=404
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    elif request.method == "POST":
        # Generate recommendations based on task type and priorities
        try:
            data = json.loads(request.body)
            task_type = data.get("task_type", "generation")
            priorities = data.get("priorities", {})

            # Map task types to categories
            task_to_category = {
                "generation": "content_creation",
                "summarization": "general",
                "coding": "coding",
                "chat": "chatbot",
            }
            category = task_to_category.get(task_type, "general")

            # Get priority weights (0-100, default 33.33 for balanced)
            cost_weight = priorities.get("low_cost", 33.33) / 100.0
            latency_weight = priorities.get("low_latency", 33.33) / 100.0
            quality_weight = priorities.get("high_quality", 33.33) / 100.0

            # Normalize weights to sum to 1.0
            total_weight = cost_weight + latency_weight + quality_weight
            if total_weight > 0:
                cost_weight /= total_weight
                latency_weight /= total_weight
                quality_weight /= total_weight

            # Query models that match the category
            models = AIModel.objects.filter(
                is_active=True, is_deprecated=False, pricing__isnull=False
            ).select_related("pricing", "provider")

            # Filter by category if available
            if connection.vendor != "sqlite":
                models = models.filter(
                    Q(categories__isnull=True)
                    | Q(categories__contains=[category])
                    | Q(categories__contains=["general"])
                )

            # Calculate scores for each model
            recommendations = []
            for model in models:
                if not model.pricing:
                    continue

                # Calculate cost score (lower is better, inverted)
                avg_cost_per_1m = float(
                    (
                        model.pricing.request_token_price
                        + model.pricing.response_token_price
                    )
                    / 2
                )
                cost_score = max(0, 100 - (avg_cost_per_1m * 10))  # Normalize to 0-100

                # Estimate speed (tokens/second) - simplified, would need actual data
                # Using context window as proxy (larger context = potentially slower)
                speed_score = 100
                if model.context_window:
                    if model.context_window < 8000:
                        speed_score = 200  # Fast
                    elif model.context_window < 32000:
                        speed_score = 120  # Medium
                    else:
                        speed_score = 90  # Slower

                # Quality score from benchmarks
                quality_score = 50  # Default
                if model.benchmark_scores:
                    # Calculate weighted average of benchmarks
                    total_score = 0
                    total_weight = 0
                    benchmark_weights = {
                        "MMLU": 0.4,
                        "HumanEval": 0.4,
                        "SWE-bench Verified": 0.2,
                    }
                    for bench_name, weight in benchmark_weights.items():
                        if bench_name in model.benchmark_scores:
                            total_score += model.benchmark_scores[bench_name] * weight
                            total_weight += weight
                    if total_weight > 0:
                        quality_score = total_score / total_weight

                # Calculate overall match score
                match_score = (
                    cost_score * cost_weight
                    + speed_score * latency_weight
                    + quality_score * quality_weight
                )

                # Format cost
                cost_str = f"${avg_cost_per_1m:.2f}"

                # Format speed
                speed_str = f"{speed_score} t/s"

                recommendations.append(
                    {
                        "name": model.display_name or model.name,
                        "provider": model.provider.name,
                        "score": round(match_score, 0),
                        "cost": cost_str,
                        "speed": speed_str,
                        "features": model.categories or [],
                        "bestFor": _get_best_for_description(model, category),
                        "model_id": model.id,
                    }
                )

            # Sort by score descending and take top 10
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            recommendations = recommendations[:10]

            return JsonResponse(
                {
                    "status": "success",
                    "data": {
                        "recommendations": recommendations,
                        "count": len(recommendations),
                    },
                }
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON"}, status=400
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


def _get_best_for_description(model, category):
    """Generate a 'best for' description based on model and category."""
    category_descriptions = {
        "coding": "Code generation & development tasks",
        "content_creation": "Content writing & generation",
        "chatbot": "Conversational AI & chat applications",
        "general": "General purpose tasks",
    }

    base_desc = category_descriptions.get(category, "General purpose tasks")

    if model.has_reasoning:
        return f"Complex reasoning & {base_desc}"
    elif model.supports_tools:
        return f"Tool-using applications & {base_desc}"
    else:
        return base_desc


@csrf_exempt
@require_http_methods(["POST"])
def generate_recommendations_for_app(request):
    """Generate recommendations for a specific application by running analysis."""
    try:
        data = json.loads(request.body)
        application_id = data.get("application_id")
        clear_existing = data.get(
            "clear_existing", True
        )  # Default to clearing old recommendations

        if not application_id:
            return JsonResponse(
                {"status": "error", "message": "application_id is required"}, status=400
            )

        # Get the application
        try:
            app = Application.objects.get(application_id=application_id)
        except Application.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Application not found"}, status=404
            )

        # Check if application has traces
        trace_count = LLMTrace.objects.filter(application=app).count()
        if trace_count == 0:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "No usage data found for this application. Please ingest some traces first.",
                },
                status=400,
            )

        # Clear existing recommendations if requested
        old_count = 0
        if clear_existing:
            old_count = Recommendation.objects.filter(
                application=app, is_active=True
            ).count()
            Recommendation.objects.filter(application=app, is_active=True).update(
                is_active=False
            )

        # Run usage analysis
        analyzer = UsageAnalyzer(analysis_period_days=30)
        analyses = analyzer.analyze_application(app)

        if not analyses:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "No usage analysis could be generated. Make sure there are traces within the last 30 days.",
                },
                status=400,
            )

        # Generate recommendations for each analysis
        rec_engine = RecommendationEngine()
        total_recommendations = 0

        for analysis in analyses:
            recs = rec_engine.generate_recommendations(analysis, max_recommendations=10)
            total_recommendations += len(recs)

        # Get the newly generated recommendations
        recommendations = (
            Recommendation.objects.filter(
                application=app, is_active=True, is_dismissed=False
            )
            .select_related("recommended_model", "recommended_model__provider")
            .order_by("-confidence_score")
        )

        recs_data = []
        for rec in recommendations[:20]:
            recs_data.append(
                {
                    "id": rec.id,
                    "application_id": rec.application.application_id,
                    "application_name": rec.application.name,
                    "current_model": rec.current_model_name,
                    "recommended_model": rec.recommended_model.name
                    if rec.recommended_model
                    else None,
                    "provider": rec.recommended_model.provider.name
                    if rec.recommended_model
                    else None,
                    "recommendation_type": rec.recommendation_type,
                    "confidence_score": float(rec.confidence_score),
                    "cost_savings_percent": float(rec.estimated_cost_savings_percent),
                    "monthly_savings": float(rec.estimated_monthly_savings),
                    "reasoning": rec.reasoning,
                    "test_status": rec.test_status,
                    "quality_overall_score": float(rec.quality_overall_score)
                    if rec.quality_overall_score
                    else None,
                    "features": rec.recommended_model.categories
                    if rec.recommended_model and rec.recommended_model.categories
                    else [],
                }
            )

        return JsonResponse(
            {
                "status": "success",
                "message": f"Generated {total_recommendations} new recommendations",
                "data": {
                    "recommendations": recs_data,
                    "count": len(recs_data),
                    "analyses_created": len(analyses),
                    "old_recommendations_cleared": old_count,
                    "new_recommendations_generated": total_recommendations,
                },
            }
        )
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_http_methods(["GET"])
def dashboard_stats(request):
    """Get dashboard statistics."""
    try:
        total_applications = Application.objects.filter(is_active=True).count()

        # Get stats from traces using DB aggregation
        traces = LLMTrace.objects.all()
        total_requests = traces.count()
        agg = traces.aggregate(
            total_cost=Sum("total_cost"), total_tokens=Sum("total_token_count")
        )
        total_cost = float(agg["total_cost"] or 0)
        total_tokens = agg["total_tokens"] or 0

        # Get active recommendations
        active_recommendations = Recommendation.objects.filter(
            is_active=True, is_dismissed=False
        ).count()

        # Get applications with recommendations
        apps_with_recommendations = (
            Application.objects.filter(
                recommendations__is_active=True, recommendations__is_dismissed=False
            )
            .distinct()
            .count()
        )

        return JsonResponse(
            {
                "status": "success",
                "data": {
                    "total_applications": total_applications,
                    "total_requests": total_requests,
                    "total_cost": float(total_cost),
                    "total_tokens": total_tokens,
                    "active_recommendations": active_recommendations,
                    "apps_with_recommendations": apps_with_recommendations,
                },
            }
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
