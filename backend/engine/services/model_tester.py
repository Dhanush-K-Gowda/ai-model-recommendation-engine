import time
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from portkey_ai import Portkey
import requests

from engine.models import AIModel, LLMTrace, Recommendation, Pricing

# Set up logger
logger = logging.getLogger(__name__)


# Initialize Portkey client
def get_portkey_client():
    """Get Portkey client with API key from settings or environment."""
    api_key = getattr(settings, 'PORTKEY_API_KEY', None)
    if not api_key:
        # Try environment variable
        import os
        api_key = os.environ.get('PORTKEY_API_KEY', '17Kpc3zpdJeS9aptj7LBm7Tv1x+x')
    return Portkey(api_key=api_key)


# Provider name mapping: Database provider name -> Portkey provider name
PROVIDER_MAP = {
    'open-ai': 'openai',
    'openai': 'openai',
    'azure-openai': 'openai',
    'azure': 'openai',  # Azure OpenAI uses OpenAI format
    'anthropic': 'anthropic',
    'google': 'google',
    'vertex-ai': 'google',
    # Add more mappings as needed
}


def extract_error_reason(exception):
    """Extract specific error reason and status from exception."""
    error_str = str(exception).lower()
    
    # Check for deprecated models (must check before other 404 checks)
    if 'deprecated' in error_str:
        return 'model_deprecated', "Model has been deprecated"
    
    # Check for HTTP status codes
    if '403' in error_str or 'forbidden' in error_str:
        return 'http_403_forbidden', "HTTP 403 Forbidden"
    elif '401' in error_str or 'unauthorized' in error_str:
        return 'http_401_unauthorized', "HTTP 401 Unauthorized"
    elif '429' in error_str or 'rate limit' in error_str:
        return 'rate_limited', "Rate Limited (429)"
    
    # Check for safety/policy violations
    if 'safety' in error_str or 'filter' in error_str or 'content_filter' in error_str:
        return 'safety_filter_triggered', "Safety Filter Triggered"
    elif 'policy' in error_str or 'violation' in error_str:
        return 'provider_policy_violation', "Provider Policy Violation"
    elif 'refused' in error_str:
        return 'request_refused', "Request Refused"
    
    # Check for timeout
    if 'timeout' in error_str or 'timed out' in error_str:
        return 'timeout', "Timeout"
    elif 'connection' in error_str:
        return 'connection_error', "Connection Error"
    
    # Default
    return 'error', f"Error: {str(exception)[:100]}"


def map_provider_to_portkey(provider_name: str) -> str:
    """Map database provider name to Portkey provider name."""
    provider_lower = provider_name.lower().strip()
    return PROVIDER_MAP.get(provider_lower, provider_lower)


def get_model_name_for_portkey(aimodel: AIModel) -> str:
    """Get model name in format expected by Portkey."""
    # Use the model name as-is, may need adjustments for specific models
    return aimodel.name


def call_model_via_portkey(prompt: str, aimodel: AIModel, max_tokens: int = 4096) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Call model API via Portkey.
    
    Returns:
        Tuple of (response_dict, error_message)
        response_dict contains: content, input_tokens, output_tokens, total_tokens, latency_sec
    """
    portkey = get_portkey_client()
    
    try:
        provider_name = aimodel.provider.name
        portkey_provider = map_provider_to_portkey(provider_name)
        model_name = get_model_name_for_portkey(aimodel)
        model_path = f"@{portkey_provider}/{model_name}"
        
        start_time = time.time()
        
        if portkey_provider.lower() == "anthropic":
            # Anthropic requires max_tokens
            response = portkey.chat.completions.create(
                model=model_path,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens
            )
        else:
            # OpenAI and other providers
            response = portkey.chat.completions.create(
                model=model_path,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        
        latency_sec = time.time() - start_time
        
        return {
            'content': response.choices[0].message.content,
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
            'latency_sec': latency_sec,
            'status': 'success'
        }, None
        
    except requests.exceptions.Timeout:
        latency_sec = time.time() - start_time if 'start_time' in locals() else 0
        return {
            'content': '',
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'latency_sec': latency_sec,
            'status': 'timeout'
        }, 'Request timed out'
        
    except Exception as e:
        latency_sec = time.time() - start_time if 'start_time' in locals() else 0
        status, reason = extract_error_reason(e)
        
        # Auto-mark as deprecated if detected
        if status == 'model_deprecated':
            if not aimodel.is_deprecated:
                aimodel.is_deprecated = True
                aimodel.save(update_fields=['is_deprecated'])
                logger.warning(f"  ⚠ Marked model as deprecated: {aimodel.name} ({aimodel.provider.name})")
        
        logger.error(f"  ✗ Error: {status} - {reason}")
        logger.debug(f"  Exception details: {str(e)}")
        return {
            'content': '',
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'latency_sec': latency_sec,
            'status': status
        }, reason


def get_test_prompts(application, current_model_name: str, sample_size: int = 20) -> List[LLMTrace]:
    """
    Get sample prompts from traces for the current model.
    
    Returns:
        List of LLMTrace objects with prompts
    """
    traces = LLMTrace.objects.filter(
        application=application,
        raw_model_name__iexact=current_model_name,
        prompt__isnull=False
    ).exclude(prompt='').order_by('-traced_at')[:sample_size * 2]  # Get more to filter
    
    # Filter to only traces with non-empty prompts
    valid_traces = [t for t in traces if t.prompt.strip()]
    
    # Return up to sample_size
    return valid_traces[:sample_size]


def calculate_cost(input_tokens: int, output_tokens: int, pricing: Pricing) -> Decimal:
    """Calculate cost based on token counts and pricing."""
    if not pricing:
        return Decimal('0')
    
    input_cost = Decimal(str(input_tokens)) * pricing.request_token_price / Decimal('1000000')
    output_cost = Decimal(str(output_tokens)) * pricing.response_token_price / Decimal('1000000')
    return input_cost + output_cost


def evaluate_quality_single(prompt: str, current_response: str, recommended_response: str) -> Optional[Dict[str, float]]:
    """
    Evaluate quality of recommended response vs current response using LLM-as-judge.
    
    Returns:
        Dict with quality scores or None if evaluation fails
    """
    portkey = get_portkey_client()
    
    try:
        evaluation_prompt = f"""
You are an expert evaluator. Compare the original model's response with the new model's response for the given prompt.

PROMPT: {prompt[:500]}

ORIGINAL RESPONSE: {current_response[:500]}

NEW MODEL RESPONSE: {recommended_response[:500]}

Rate the new model response on a scale of 0-10 for each dimension:
- 0 = No match/Poor
- 4 = Low match/Weak
- 7 = Medium match/Good
- 10 = High match/Excellent

Provide scores in this exact format (only numbers):
Correctness: [0-10]
Completeness: [0-10]
Relevance: [0-10]
Instruction Adherence: [0-10]
Groundedness: [0-10]
Conciseness: [0-10]

Do not include any other text.
"""
        
        judge_response = portkey.chat.completions.create(
            model="@anthropic/claude-sonnet-4-5-20250929",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert evaluator. Provide scores in the specified format only."
                },
                {
                    "role": "user",
                    "content": evaluation_prompt
                }
            ],
            max_tokens=2000
        )
        
        scores_text = judge_response.choices[0].message.content
        scores = {}
        
        # Parse scores
        score_lines = scores_text.strip().split('\n')
        for line in score_lines:
            if ':' in line:
                dimension, score = line.split(':', 1)
                dimension = dimension.strip().lower().replace(' ', '_')
                try:
                    score_val = float(score.strip())
                    scores[dimension] = score_val
                except:
                    pass
        
        return scores if scores else None
        
    except Exception as e:
        return None


def test_recommendation(recommendation: Recommendation, sample_size: int = 20, evaluate_quality: bool = True) -> Dict:
    """
    Test a recommendation by running prompts through both current and recommended models.
    
    Args:
        recommendation: Recommendation object to test
        sample_size: Number of prompts to test (default 20)
        evaluate_quality: Whether to perform LLM-as-judge quality evaluation
    
    Returns:
        Dict with test results
    """
    application = recommendation.application
    current_model_name = recommendation.current_model_name
    recommended_model = recommendation.recommended_model
    
    # Get test prompts
    test_traces = get_test_prompts(application, current_model_name, sample_size)
    
    if not test_traces:
        return {
            'status': 'failed',
            'error': 'No test prompts found for current model'
        }
    
    # Get pricing for recommended model
    recommended_pricing = Pricing.objects.filter(model=recommended_model).first()
    if not recommended_pricing:
        return {
            'status': 'failed',
            'error': 'No pricing data found for recommended model'
        }
    
    # Get current model for comparison
    current_model = recommendation.usage_analysis.model
    current_pricing = None
    if current_model:
        current_pricing = Pricing.objects.filter(model=current_model).first()
    
    # Test results storage
    current_results = []
    recommended_results = []
    quality_evaluations = []
    
    # Test each prompt
    for trace in test_traces:
        prompt = trace.prompt
        
        # Test current model (if available) - use trace response as baseline
        current_result = None
        if current_model and current_pricing:
            current_result, error = call_model_via_portkey(
                prompt, 
                current_model,
                max_tokens=current_model.context_window or 4096
            )
            if current_result:
                if current_pricing:
                    current_result['cost'] = float(calculate_cost(
                        current_result['input_tokens'],
                        current_result['output_tokens'],
                        current_pricing
                    ))
                current_results.append(current_result)
            else:
                # API call failed, use trace data as fallback
                if trace.status == 'success':
                    current_result = {
                        'content': trace.response,
                        'input_tokens': trace.input_token_count,
                        'output_tokens': trace.output_token_count,
                        'total_tokens': trace.total_token_count,
                        'latency_sec': trace.estimated_latency_sec or 0,
                        'cost': float(trace.total_cost),
                        'status': 'success'
                    }
                    current_results.append(current_result)
            time.sleep(0.5)  # Rate limiting
        else:
            # Use trace data as baseline if model not available
            if trace.status == 'success':
                current_result = {
                    'content': trace.response,
                    'input_tokens': trace.input_token_count,
                    'output_tokens': trace.output_token_count,
                    'total_tokens': trace.total_token_count,
                    'latency_sec': trace.estimated_latency_sec or 0,
                    'cost': float(trace.total_cost),
                    'status': 'success'
                }
                current_results.append(current_result)
        
        # Test recommended model
        recommended_result, error = call_model_via_portkey(
            prompt,
            recommended_model,
            max_tokens=recommended_model.context_window or 4096
        )
        if recommended_result:
            if recommended_pricing:
                recommended_result['cost'] = float(calculate_cost(
                    recommended_result['input_tokens'],
                    recommended_result['output_tokens'],
                    recommended_pricing
                ))
            recommended_results.append(recommended_result)
        else:
            recommended_results.append({
                'content': '',
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'latency_sec': 0,
                'cost': 0,
                'status': 'failed'
            })
        
        # Quality evaluation if both responses available
        if evaluate_quality:
            # Use trace response if current_result not available from API call
            current_response = None
            if current_result and current_result.get('status') == 'success':
                current_response = current_result['content']
            elif trace.status == 'success' and trace.response:
                current_response = trace.response
            
            if current_response and recommended_result and recommended_result.get('status') == 'success':
                quality_scores = evaluate_quality_single(
                    prompt,
                    current_response,
                    recommended_result['content']
                )
                if quality_scores:
                    quality_evaluations.append(quality_scores)
        
        time.sleep(0.5)  # Rate limiting
    
    # Calculate metrics
    # Current model metrics (use trace data if API calls failed)
    if current_results:
        current_successful = [r for r in current_results if r and r.get('status') == 'success']
        current_avg_latency = sum(r['latency_sec'] for r in current_successful) / len(current_successful) if current_successful else 0
        current_avg_cost = sum(r.get('cost', 0) for r in current_successful) / len(current_successful) if current_successful else 0
        current_success_rate = (len(current_successful) / len(current_results) * 100) if current_results else 0
    else:
        # Fallback to trace data
        successful_traces = [t for t in test_traces if t.status == 'success']
        current_avg_latency = sum(t.estimated_latency_sec or 0 for t in successful_traces) / len(successful_traces) if successful_traces else 0
        current_avg_cost = sum(float(t.total_cost) for t in successful_traces) / len(successful_traces) if successful_traces else 0
        current_success_rate = (len(successful_traces) / len(test_traces) * 100) if test_traces else 0
    
    # Recommended model metrics
    recommended_successful = [r for r in recommended_results if r and r.get('status') == 'success']
    recommended_avg_latency = sum(r['latency_sec'] for r in recommended_successful) / len(recommended_successful) if recommended_successful else 0
    recommended_avg_cost = sum(r.get('cost', 0) for r in recommended_successful) / len(recommended_successful) if recommended_successful else 0
    recommended_success_rate = (len(recommended_successful) / len(test_traces) * 100) if test_traces else 0
    
    # Calculate comparisons
    latency_comparison_pct = 0
    if current_avg_latency > 0:
        latency_comparison_pct = ((recommended_avg_latency - current_avg_latency) / current_avg_latency) * 100
    
    cost_comparison_pct = 0
    if current_avg_cost > 0:
        cost_comparison_pct = ((recommended_avg_cost - current_avg_cost) / current_avg_cost) * 100
    
    # Quality scores
    quality_scores = {}
    quality_overall_score = None
    quality_comparison = {}
    
    if quality_evaluations:
        # Calculate average quality scores
        dimensions = ['correctness', 'completeness', 'relevance', 'instruction_adherence', 'groundedness', 'conciseness']
        for dimension in dimensions:
            scores = [q.get(dimension, 0) for q in quality_evaluations if dimension in q]
            if scores:
                quality_scores[dimension] = sum(scores) / len(scores)
        
        if quality_scores:
            quality_overall_score = sum(quality_scores.values()) / len(quality_scores)
    
    return {
        'status': 'completed',
        'test_samples_count': len(test_traces),
        'actual_avg_latency_sec': recommended_avg_latency,
        'actual_avg_cost_per_request': Decimal(str(recommended_avg_cost)),
        'actual_success_rate': recommended_success_rate,
        'quality_scores': quality_scores,
        'quality_overall_score': quality_overall_score,
        'quality_comparison': quality_comparison,  # Could be enhanced to compare vs current
        'latency_comparison_pct': latency_comparison_pct,
        'cost_comparison_pct': cost_comparison_pct,
        'current_metrics': {
            'avg_latency': current_avg_latency,
            'avg_cost': current_avg_cost,
            'success_rate': current_success_rate
        }
    }

