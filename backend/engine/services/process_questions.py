import csv
import time
from portkey_ai import Portkey
import requests
import json

# Initialize Portkey client
portkey = Portkey(
    api_key="" # move to env
)

# Model Configuration
MODELS_CONFIG = {
    "openai_gpt4o": {
        "provider": "openai",
        "model": "gpt-4o",
        "input_cost": 0.000005,
        "output_cost": 0.000015,
        "max_tokens": 4096
    },
    "anthropic_opus": {
        "provider": "anthropic",
        "model": "claude-4-opus-20250514",
        "input_cost": 0.000015,
        "output_cost": 0.000075,
        "max_tokens": 4096
    },
    "anthropic_sonnet": {
        "provider": "anthropic",
        "model": "Claude-3-7-Sonnet-20250219",
        "input_cost": 0.000003,
        "output_cost": 0.000015,
        "max_tokens": 4096
    }
}

def call_model_api(prompt, provider, model, max_tokens=4096):
    """
    Call LLM API with provider-specific request body handling.
    
    Args:
        prompt: The prompt to send
        provider: Provider name (openai, anthropic, etc.)
        model: Model name
        max_tokens: Maximum tokens to generate
        
    Returns:
        Response object or None if error
    """
    try:
        model_path = f"@{provider}/{model}"
        
        if provider.lower() == "anthropic":
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
        
        return response
    except Exception as e:
        raise e

def extract_error_reason(exception):
    """Extract specific error reason and status from exception"""
    error_str = str(exception).lower()
    
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

# def process_questions(data, provider, model, input_cost, output_cost, output_csv="gpt4o_responses.csv"):

def process_questions(data, provider, model, input_cost, output_cost, output_csv="gpt4o_responses.csv"):
    """
    Process questions and send to LLM via Portkey, tracking responses and costs.
    
    Args:
        data: List of rows from CSV (dictionaries)
        provider: Provider name (e.g., 'openai', 'anthropic')
        model: Model name (e.g., 'gpt-4o', 'claude-3-opus')
        input_cost: Cost per input token
        output_cost: Cost per output token
        output_csv: Output CSV filename
    """
    
    print(f"Starting processing with {provider}/{model}")
    print(f"Input cost: ${input_cost}/token, Output cost: ${output_cost}/token")
    
    # Get max_tokens from config if available
    config_key = f"{provider}_{model.replace('-', '_')}"
    max_tokens = MODELS_CONFIG.get(config_key, {}).get('max_tokens', 4096)
    
    # Prepare output file
    output_file = open(output_csv, 'w', newline='', encoding='utf-8')
    output_writer = csv.writer(output_file)
    
    # Write header
    output_writer.writerow([
        'id',
        'original_model',
        'prompt',
        'response',
        'input_tokens',
        'output_tokens',
        'total_tokens',
        'input_cost_usd',
        'output_cost_usd',
        'total_cost_usd',
        'latency_ms',
        'status',
        'reason'
    ])
    
    # total_processed = len(data)
    data = data[:40]  # Limit to first 40 records
    print(f"Processing {len(data)} records...\n")
    total_processed = len(data)
    # Process each question
    for idx, row in enumerate(data, 1):
        prompt = row.get('prompt', '')
        
        if not prompt:
            print(f"Row {idx}: Skipping empty prompt")
            continue
        
        print(f"Processing {idx}/{total_processed}: {prompt[:50]}...")
        
        start_time = time.time()
        
        try:
            # Call LLM via provider-specific dispatcher
            response = call_model_api(prompt, provider, model, max_tokens)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract response and token information
            answer = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Calculate costs
            input_cost_usd = round(input_tokens * input_cost, 6)
            output_cost_usd = round(output_tokens * output_cost, 6)
            total_cost_usd = round(input_cost_usd + output_cost_usd, 6)
            
            # Write successful response
            output_writer.writerow([
                row.get('id', ''),
                row.get('model_name', ''),
                prompt,
                answer,
                input_tokens,
                output_tokens,
                total_tokens,
                input_cost_usd,
                output_cost_usd,
                total_cost_usd,
                round(latency_ms, 2),
                'success',
                ''
            ])
            
            print(f"  ✓ Success - Latency: {latency_ms:.2f}ms - Cost: ${total_cost_usd:.6f}")
            
        except requests.exceptions.Timeout:
            latency_ms = (time.time() - start_time) * 1000
            print(f"  ✗ Timeout - Latency: {latency_ms:.2f}ms")
            output_writer.writerow([
                row.get('id', ''),
                row.get('model_name', ''),
                prompt,
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                round(latency_ms, 2),
                'timeout',
                'Request timed out'
            ])
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            status, reason = extract_error_reason(e)
            
            print(f"  ✗ {status.upper()} - {reason} - Latency: {latency_ms:.2f}ms")
            
            output_writer.writerow([
                row.get('id', ''),
                row.get('model_name', ''),
                prompt,
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                round(latency_ms, 2),
                status,
                reason
            ])
        
        output_file.flush()
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    output_file.close()
    print(f"\nProcessing complete! Results saved to {output_csv}")


def evaluate_responses(input_csv, gpt4o_csv, evaluation_output="evaluation_report.csv"):
    """
    Evaluate GPT-4o responses against original model responses.
    
    3-part evaluation:
    1. Performance metrics (latency, cost, error analysis)
    2. Quality assessment (LLM judge on 6 dimensions)
    3. Comprehensive insights and trade-offs
    
    Args:
        input_csv: Path to input dataset (1k_data_with_tokens_latency_cost.csv)
        gpt4o_csv: Path to GPT-4o responses (gpt4o_responses.csv)
        evaluation_output: Output CSV for detailed evaluation results
    """
    
    print("\n" + "="*80)
    print("STARTING COMPREHENSIVE EVALUATION")
    print("="*80)
    
    # Load both datasets
    input_data = {}
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize keys by stripping whitespace
            normalized_row = {k.strip(): v for k, v in row.items()}
            row_id = normalized_row.get('id')
            if row_id:
                input_data[row_id] = normalized_row
    
    gpt4o_data = {}
    successful_responses = {}
    with open(gpt4o_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize keys by stripping whitespace
            normalized_row = {k.strip(): v for k, v in row.items()}
            row_id = normalized_row.get('id')
            if row_id:
                gpt4o_data[row_id] = normalized_row
                # Only consider successful responses for quality evaluation
                if normalized_row.get('status') == 'success':
                    successful_responses[row_id] = normalized_row
    
    print(f"\nLoaded {len(input_data)} original responses")
    print(f"Loaded {len(gpt4o_data)} model responses")
    print(f"Successful responses for evaluation: {len(successful_responses)}")
    
    # ===== PART 1: PERFORMANCE METRICS =====
    print("\n" + "-"*80)
    print("PART 1: PERFORMANCE METRICS")
    print("-"*80)
    
    # Latency comparison
    original_latencies = []
    model_latencies = []
    
    for id, model_row in gpt4o_data.items():
        if id in input_data:
            orig = input_data[id]
            try:
                orig_latency = float(orig.get('estimated_latency_sec', 0))
                model_latency = float(model_row.get('latency_ms', 0)) / 1000  # Convert to seconds
                original_latencies.append(orig_latency)
                model_latencies.append(model_latency)
            except:
                pass
    
    avg_original_latency = sum(original_latencies) / len(original_latencies) if original_latencies else 0
    avg_model_latency = sum(model_latencies) / len(model_latencies) if model_latencies else 0
    latency_change_pct = ((avg_model_latency - avg_original_latency) / avg_original_latency * 100) if avg_original_latency > 0 else 0
    
    print(f"\nLatency Analysis:")
    print(f"  Original Model Avg Latency: {avg_original_latency:.4f}s")
    print(f"  New Model Avg Latency: {avg_model_latency:.4f}s")
    print(f"  Change: {latency_change_pct:+.2f}%")
    
    # Cost comparison
    original_costs = []
    model_costs = []
    
    for id, model_row in gpt4o_data.items():
        if id in input_data:
            orig = input_data[id]
            try:
                orig_cost = float(orig.get('total_cost', 0))
                model_cost = float(model_row.get('total_cost_usd', 0))
                original_costs.append(orig_cost)
                model_costs.append(model_cost)
            except:
                pass
    
    avg_original_cost = sum(original_costs) / len(original_costs) if original_costs else 0
    avg_model_cost = sum(model_costs) / len(model_costs) if model_costs else 0
    cost_change_pct = ((avg_model_cost - avg_original_cost) / avg_original_cost * 100) if avg_original_cost > 0 else 0
    
    print(f"\nCost Analysis:")
    print(f"  Original Model Avg Cost: ${avg_original_cost:.6f}")
    print(f"  New Model Avg Cost: ${avg_model_cost:.6f}")
    print(f"  Change: {cost_change_pct:+.2f}%")
    
    # Error analysis
    orig_success_count = sum(1 for row in input_data.values() if row.get('status_code') == 'success')
    orig_error_count = len(input_data) - orig_success_count
    orig_error_rate = (orig_error_count / len(input_data) * 100) if len(input_data) > 0 else 0
    
    model_success_count = sum(1 for row in gpt4o_data.values() if row.get('status') == 'success')
    model_error_count = len(gpt4o_data) - model_success_count
    model_error_rate = (model_error_count / len(gpt4o_data) * 100) if len(gpt4o_data) > 0 else 0
    
    print(f"\nError Analysis:")
    print(f"  Original Model Success Rate: {100-orig_error_rate:.2f}% ({orig_success_count}/{len(input_data)})")
    print(f"  New Model Success Rate: {100-model_error_rate:.2f}% ({model_success_count}/{len(gpt4o_data)})")
    print(f"  Error Rate Change: {model_error_rate - orig_error_rate:+.2f} percentage points")
    
    # ===== PART 2: QUALITY ASSESSMENT =====
    print("\n" + "-"*80)
    print("PART 2: QUALITY ASSESSMENT (LLM as Judge)")
    print("-"*80)
    
    quality_scores = {
        'correctness': [],
        'completeness': [],
        'relevance': [],
        'instruction_adherence': [],
        'groundedness': [],
        'conciseness': []
    }
    
    sample_size = min(len(successful_responses), 10)  # Evaluate up to 10 successful responses
    evaluated_count = 0
    
    print(f"\nEvaluating {sample_size} successful responses using Claude as judge...")
    
    for idx, (id, model_row) in enumerate(list(successful_responses.items())[:sample_size]):
        if id not in input_data:
            continue
        
        orig_row = input_data[id]
        prompt = orig_row.get('prompt', '')
        original_response = orig_row.get('response', '')
        model_response = model_row.get('response', '')
        
        if not prompt or not original_response or not model_response:
            continue
        
        try:
            # Use Claude as judge
            evaluation_prompt = f"""
You are an expert evaluator. Compare the original model's response with the new model's response for the given prompt.

PROMPT: {prompt[:500]}

ORIGINAL RESPONSE: {original_response[:500]}

NEW MODEL RESPONSE: {model_response[:500]}

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
            
            # Parse scores
            score_lines = scores_text.strip().split('\n')
            for line in score_lines:
                if ':' in line:
                    dimension, score = line.split(':')
                    dimension = dimension.strip().lower().replace(' ', '_')
                    try:
                        score_val = int(score.strip())
                        if dimension in quality_scores:
                            quality_scores[dimension].append(score_val)
                    except:
                        pass
            
            evaluated_count += 1
            print(f"  ✓ Evaluated sample {evaluated_count}/{sample_size}")
            
        except Exception as e:
            print(f"  ✗ Error evaluating response {id}: {str(e)}")
            continue
    
    # Calculate average quality scores
    print(f"\nQuality Evaluation Results (based on {evaluated_count} samples):")
    avg_quality_scores = {}
    for dimension, scores in quality_scores.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        avg_quality_scores[dimension] = avg_score
        print(f"  {dimension.replace('_', ' ').title()}: {avg_score:.2f}/10")
    
    overall_quality = sum(avg_quality_scores.values()) / len(avg_quality_scores) if avg_quality_scores else 0
    print(f"  Overall Quality Score: {overall_quality:.2f}/10")
    
    # ===== PART 3: COMPREHENSIVE INSIGHTS =====
    print("\n" + "-"*80)
    print("PART 3: COMPREHENSIVE INSIGHTS & RECOMMENDATIONS")
    print("-"*80)
    
    # ===== PART 3B: ASK LLM FOR COMPREHENSIVE SYNTHESIS =====
    print(f"\nGenerating comprehensive insights using Claude...")
    
    # Prepare detailed metrics for Claude synthesis
    metrics_summary = f"""
EVALUATION METRICS SUMMARY:

Performance Metrics:
- Original Model Avg Latency: {avg_original_latency:.4f}s
- New Model Avg Latency: {avg_model_latency:.4f}s
- Latency Change: {latency_change_pct:+.2f}%

- Original Model Avg Cost: ${avg_original_cost:.6f}
- New Model Avg Cost: ${avg_model_cost:.6f}
- Cost Change: {cost_change_pct:+.2f}%

- Original Model Success Rate: {100-orig_error_rate:.2f}% ({orig_success_count}/{len(input_data)} successful)
- New Model Success Rate: {100-model_error_rate:.2f}% ({model_success_count}/{len(gpt4o_data)} successful)
- Reliability Change: {model_error_rate - orig_error_rate:+.2f} percentage points

Quality Assessment (based on {evaluated_count} successful response samples):
- Correctness: {avg_quality_scores.get('correctness', 0):.2f}/10
- Completeness: {avg_quality_scores.get('completeness', 0):.2f}/10
- Relevance: {avg_quality_scores.get('relevance', 0):.2f}/10
- Instruction Adherence: {avg_quality_scores.get('instruction_adherence', 0):.2f}/10
- Groundedness: {avg_quality_scores.get('groundedness', 0):.2f}/10
- Conciseness: {avg_quality_scores.get('conciseness', 0):.2f}/10
- Overall Quality Score: {overall_quality:.2f}/10
"""
    
    try:
        synthesis_prompt = f"""
{metrics_summary}

Generate ONE-LINE summary only for comparing this model to the baseline:
Format: "[Quality change description]. [Latency change]. [Cost change]. [Reliability change]."

For costs: If cost is higher, state clearly "Cost increased by X%". Do NOT say manageable.
Be factual and direct. Use actual numbers from metrics above.
"""
        
        synthesis_response = portkey.chat.completions.create(
            model="@anthropic/claude-sonnet-4-5-20250929",
            messages=[
                {
                    "role": "system",
                    "content": "Generate only the one-line summary. Be direct about costs without saying manageable. No explanations."
                },
                {
                    "role": "user",
                    "content": synthesis_prompt
                }
            ],
            max_tokens=500
        )
        
        comprehensive_statement = synthesis_response.choices[0].message.content.strip()
        print(f"\nComprehensive Statement:")
        print(f"  {comprehensive_statement}")
        
    except Exception as e:
        print(f"Error generating comprehensive synthesis: {str(e)}")
    
    print("\n" + "="*80)
    print("EVALUATION COMPLETE")
    print("="*80 + "\n")
    
    return {
        'overall_quality': overall_quality,
        'cost_change_pct': cost_change_pct,
        'latency_change_pct': latency_change_pct,
        'reliability_change_pct': model_error_rate - orig_error_rate,
        'comprehensive_statement': comprehensive_statement if 'comprehensive_statement' in locals() else ""
    }

def run_multi_model_evaluation(input_csv, models_to_evaluate):
    """
    Run evaluation across multiple models and generate comprehensive comparison.
    
    Args:
        input_csv: Path to input dataset
        models_to_evaluate: List of model config keys to evaluate (e.g., ['openai_gpt4o', 'anthropic_opus'])
    
    Returns:
        Dictionary with evaluation results for each model
    """
    
    print("\n" + "="*80)
    print("MULTI-MODEL EVALUATION")
    print("="*80)
    
    # Load input data
    input_data = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        input_data = list(reader)
    
    print(f"\nLoaded {len(input_data)} records from input dataset")
    
    model_results = {}
    comprehensive_statements = []  # List of tuples: (model_name, statement)
    
    # Process each model
    for model_key in models_to_evaluate:
        if model_key not in MODELS_CONFIG:
            print(f"⚠ Model '{model_key}' not found in MODELS_CONFIG. Skipping...")
            continue
        
        config = MODELS_CONFIG[model_key]
        provider = config['provider']
        model = config['model']
        input_cost = config['input_cost']
        output_cost = config['output_cost']
        
        print(f"\n{'='*80}")
        print(f"Processing model: {provider}/{model}")
        print(f"{'='*80}")
        
        # Output file name for this model
        output_csv = f"responses_{model_key}.csv"
        
        # Process questions for this model
        process_questions(input_data, provider, model, input_cost, output_cost, output_csv)
        
        # Evaluate this model's responses and capture result
        print(f"\nEvaluating {provider}/{model}...")
        eval_result = evaluate_responses(input_csv, output_csv, f"evaluation_{model_key}.csv")
        
        # Store comprehensive statement with actual model name
        model_display_name = f"{provider}/{model}" if provider != 'openai' else model
        comprehensive_statements.append((model_display_name, eval_result['comprehensive_statement']))
        
        model_results[model_key] = {
            'provider': provider,
            'model': model,
            'output_csv': output_csv,
            'evaluation_csv': f"evaluation_{model_key}.csv",
            'evaluation_metrics': eval_result
        }
    
    # Generate final synthesis across all models
    print(f"\n{'='*80}")
    print("FINAL SYNTHESIS: COMPARING ALL MODELS")
    print(f"{'='*80}")
    
    # Build dynamic evaluation reports from all comprehensive statements with actual model names
    evaluation_reports = "\n".join([
        f"{model_name}: {statement}"
        for model_name, statement in comprehensive_statements
    ])
    
    final_synthesis_prompt = f"""
The following are individual evaluation reports for the models assessed:

{evaluation_reports}

Based on these evaluations:
1. Recommend ONE model to use (state model name directly)
2. Provide reasoning in ONE sentence

Example: "Use gpt-4o because it offers best quality (9.2/10) despite 12% higher cost."

Be direct and data-driven.
"""
    
    try:
        synthesis_response = portkey.chat.completions.create(
            model="@anthropic/claude-sonnet-4-5-20250929",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at comparing LLM models. Provide ONE sentence only: which model to use and why. Be direct."
                },
                {
                    "role": "user",
                    "content": final_synthesis_prompt
                }
            ],
            max_tokens=500
        )
        
        final_recommendation = synthesis_response.choices[0].message.content.strip()
        print(f"\n🎯 RECOMMENDATION: {final_recommendation}")
        
        # Save both the final recommendation and detailed reasoning
        detailed_report = f"""FINAL MODEL COMPARISON REPORT
================================

DETAILED EVALUATION REPORTS:
{evaluation_reports}

FINAL RECOMMENDATION:
{final_recommendation}
"""
        
        with open("final_model_comparison.txt", "w") as f:
            f.write(detailed_report)
        
        print("\n✓ Full report saved to final_model_comparison.txt")
        
    except Exception as e:
        print(f"Error generating final synthesis: {str(e)}")
    
    return model_results


# Main execution
if __name__ == "__main__":
    # Read the dataset
    input_csv = "/Users/sumanacharya0075/developer/portkey_hackathon/model-recommendation-engine/backend/1k_data_with_tokens_latency_cost.csv"
    
    rows_data = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows_data = list(reader)
    
    print(f"Found {len(rows_data)} questions to process")
    
    # Limit to 40 records
    rows_data = rows_data[:40]
    print(f"Processing first {len(rows_data)} records\n")
    
    # ===== MULTI-MODEL EVALUATION =====
    # Define which models to evaluate
    models_to_evaluate = [
        "openai_gpt4o",
        "anthropic_opus",
        "anthropic_sonnet"
    ]
    
    # Run multi-model evaluation
    results = run_multi_model_evaluation(input_csv, models_to_evaluate)

