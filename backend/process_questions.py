import csv
import time
from portkey_ai import Portkey
import requests

# Initialize Portkey client
portkey = Portkey(
    api_key="17Kpc3zpdJeS9aptj7LBm7Tv1x+x"
)

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
#     """
#     Process questions and send to LLM via Portkey, tracking responses and costs.
    
#     Args:
#         data: List of rows from CSV (dictionaries)
#         provider: Provider name (e.g., 'openai')
#         model: Model name (e.g., 'gpt-4o')
#         input_cost: Cost per input token
#         output_cost: Cost per output token
#         output_csv: Output CSV filename
#     """
    
#     print(f"Starting processing with {provider}/{model}")
#     print(f"Input cost: ${input_cost}/token, Output cost: ${output_cost}/token")
    
#     # Prepare output file
#     output_file = open(output_csv, 'w', newline='', encoding='utf-8')
#     output_writer = csv.writer(output_file)
    
#     # Write header
#     output_writer.writerow([
#         'id',
#         'original_model',
#         'prompt',
#         'response',
#         'input_tokens',
#         'output_tokens',
#         'total_tokens',
#         'input_cost_usd',
#         'output_cost_usd',
#         'total_cost_usd',
#         'latency_ms',
#         'status',
#         'reason'
#     ])
    
#     total_processed = len(data)
#     model_path = f"@{provider}/{model}"
    
#     # Process each question
#     for idx, row in enumerate(data, 1):
#         prompt = row.get('prompt', '')
        
#         if not prompt:
#             print(f"Row {idx}: Skipping empty prompt")
#             continue
        
#         print(f"Processing {idx}/{total_processed}: {prompt[:50]}...")
        
#         start_time = time.time()
        
#         try:
#             # Call LLM via Portkey with dynamic provider/model
#             response = portkey.chat.completions.create(
#                 model=model_path,
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": "You are a helpful assistant."
#                     },
#                     {
#                         "role": "user",
#                         "content": prompt
#                     }
#                 ]
#             )
            
#             latency_ms = (time.time() - start_time) * 1000
            
#             # Extract response and token information
#             answer = response.choices[0].message.content
#             input_tokens = response.usage.prompt_tokens
#             output_tokens = response.usage.completion_tokens
#             total_tokens = response.usage.total_tokens
            
#             # Calculate costs
#             input_cost_usd = round(input_tokens * input_cost, 6)
#             output_cost_usd = round(output_tokens * output_cost, 6)
#             total_cost_usd = round(input_cost_usd + output_cost_usd, 6)
            
#             # Write successful response
#             output_writer.writerow([
#                 row.get('id', ''),
#                 row.get('model_name', ''),
#                 prompt,
#                 answer,
#                 input_tokens,
#                 output_tokens,
#                 total_tokens,
#                 input_cost_usd,
#                 output_cost_usd,
#                 total_cost_usd,
#                 round(latency_ms, 2),
#                 'success',
#                 ''
#             ])
            
#             print(f"  ✓ Success - Latency: {latency_ms:.2f}ms - Cost: ${total_cost_usd:.6f}")
            
#         except requests.exceptions.Timeout:
#             latency_ms = (time.time() - start_time) * 1000
#             print(f"  ✗ Timeout - Latency: {latency_ms:.2f}ms")
#             output_writer.writerow([
#                 row.get('id', ''),
#                 row.get('model_name', ''),
#                 prompt,
#                 '',
#                 '',
#                 '',
#                 '',
#                 '',
#                 '',
#                 '',
#                 round(latency_ms, 2),
#                 'timeout',
#                 'Request timed out'
#             ])
            
#         except Exception as e:
#             latency_ms = (time.time() - start_time) * 1000
#             status, reason = extract_error_reason(e)
            
#             print(f"  ✗ {status.upper()} - {reason} - Latency: {latency_ms:.2f}ms")
            
#             output_writer.writerow([
#                 row.get('id', ''),
#                 row.get('model_name', ''),
#                 prompt,
#                 '',
#                 '',
#                 '',
#                 '',
#                 '',
#                 '',
#                 '',
#                 round(latency_ms, 2),
#                 status,
#                 reason
#             ])
        
#         output_file.flush()
        
#         # Small delay to avoid rate limiting
#         time.sleep(0.5)
    
#     output_file.close()
#     print(f"\nProcessing complete! Results saved to {output_csv}")

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
            input_data[row['id']] = row
    
    gpt4o_data = {}
    successful_responses = {}
    with open(gpt4o_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            gpt4o_data[row['id']] = row
            # Only consider successful responses for quality evaluation
            if row.get('status') == 'success':
                successful_responses[row['id']] = row
    
    print(f"\nLoaded {len(input_data)} original responses")
    print(f"Loaded {len(gpt4o_data)} GPT-4o responses")
    print(f"Successful GPT-4o responses for evaluation: {len(successful_responses)}")
    
    # ===== PART 1: PERFORMANCE METRICS =====
    print("\n" + "-"*80)
    print("PART 1: PERFORMANCE METRICS")
    print("-"*80)
    
    # Latency comparison
    original_latencies = []
    gpt4o_latencies = []
    
    for id, gpt4o_row in gpt4o_data.items():
        if id in input_data:
            orig = input_data[id]
            try:
                orig_latency = float(orig.get('estimated_latency_sec', 0))
                gpt4o_latency = float(gpt4o_row.get('latency_ms', 0)) / 1000  # Convert to seconds
                original_latencies.append(orig_latency)
                gpt4o_latencies.append(gpt4o_latency)
            except:
                pass
    
    avg_original_latency = sum(original_latencies) / len(original_latencies) if original_latencies else 0
    avg_gpt4o_latency = sum(gpt4o_latencies) / len(gpt4o_latencies) if gpt4o_latencies else 0
    latency_change_pct = ((avg_gpt4o_latency - avg_original_latency) / avg_original_latency * 100) if avg_original_latency > 0 else 0
    
    print(f"\nLatency Analysis:")
    print(f"  Original Model Avg Latency: {avg_original_latency:.4f}s")
    print(f"  GPT-4o Avg Latency: {avg_gpt4o_latency:.4f}s")
    print(f"  Change: {latency_change_pct:+.2f}%")
    
    # Cost comparison
    original_costs = []
    gpt4o_costs = []
    
    for id, gpt4o_row in gpt4o_data.items():
        if id in input_data:
            orig = input_data[id]
            try:
                orig_cost = float(orig.get('total_cost', 0))
                gpt4o_cost = float(gpt4o_row.get('total_cost_usd', 0))
                original_costs.append(orig_cost)
                gpt4o_costs.append(gpt4o_cost)
            except:
                pass
    
    avg_original_cost = sum(original_costs) / len(original_costs) if original_costs else 0
    avg_gpt4o_cost = sum(gpt4o_costs) / len(gpt4o_costs) if gpt4o_costs else 0
    cost_change_pct = ((avg_gpt4o_cost - avg_original_cost) / avg_original_cost * 100) if avg_original_cost > 0 else 0
    
    print(f"\nCost Analysis:")
    print(f"  Original Model Avg Cost: ${avg_original_cost:.6f}")
    print(f"  GPT-4o Avg Cost: ${avg_gpt4o_cost:.6f}")
    print(f"  Change: {cost_change_pct:+.2f}%")
    
    # Error analysis
    orig_success_count = sum(1 for row in input_data.values() if row.get('status_code') == 'success')
    orig_error_count = len(input_data) - orig_success_count
    orig_error_rate = (orig_error_count / len(input_data) * 100) if len(input_data) > 0 else 0
    
    gpt4o_success_count = sum(1 for row in gpt4o_data.values() if row.get('status') == 'success')
    gpt4o_error_count = len(gpt4o_data) - gpt4o_success_count
    gpt4o_error_rate = (gpt4o_error_count / len(gpt4o_data) * 100) if len(gpt4o_data) > 0 else 0
    
    print(f"\nError Analysis:")
    print(f"  Original Model Success Rate: {100-orig_error_rate:.2f}% ({orig_success_count}/{len(input_data)})")
    print(f"  GPT-4o Success Rate: {100-gpt4o_error_rate:.2f}% ({gpt4o_success_count}/{len(gpt4o_data)})")
    print(f"  Error Rate Change: {gpt4o_error_rate - orig_error_rate:+.2f} percentage points")
    
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
    
    for idx, (id, gpt4o_row) in enumerate(list(successful_responses.items())[:sample_size]):
        if id not in input_data:
            continue
        
        orig_row = input_data[id]
        prompt = orig_row.get('prompt', '')
        original_response = orig_row.get('response', '')
        gpt4o_response = gpt4o_row.get('response', '')
        
        if not prompt or not original_response or not gpt4o_response:
            continue
        
        try:
            # Use Claude as judge
            evaluation_prompt = f"""
You are an expert evaluator. Compare the original model's response with GPT-4o's response for the given prompt.

PROMPT: {prompt}

ORIGINAL RESPONSE: {original_response}

GPT-4O RESPONSE: {gpt4o_response}

Rate the GPT-4o response on a scale of 0-10 for each dimension:
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
    
    # Generate insights
    insights = []
    
    # Cost impact
    if cost_change_pct < -10:
        cost_insight = f"Switching to GPT-4o reduces cost by {abs(cost_change_pct):.1f}%"
    elif cost_change_pct > 10:
        cost_insight = f"Switching to GPT-4o increases cost by {cost_change_pct:.1f}%"
    else:
        cost_insight = "Cost impact is minimal"
    
    # Quality impact
    quality_impact = ((overall_quality - 7) / 7 * 100) if overall_quality > 0 else 0  # Assuming baseline is 7/10
    if quality_impact > 5:
        quality_insight = f"Significant quality improvement (+{quality_impact:.1f}%)"
    elif quality_impact < -5:
        quality_insight = f"Quality degradation ({quality_impact:.1f}%)"
    else:
        quality_insight = "Quality remains comparable"
    
    # Latency impact
    if latency_change_pct < -10:
        latency_insight = f"Faster response times ({latency_change_pct:.1f}%)"
    elif latency_change_pct > 10:
        latency_insight = f"Slower response times (+{latency_change_pct:.1f}%)"
    else:
        latency_insight = "Latency is comparable"
    
    # Reliability impact
    error_diff = gpt4o_error_rate - orig_error_rate
    if error_diff < -2:
        reliability_insight = f"Better reliability (error rate down by {abs(error_diff):.1f}pp)"
    elif error_diff > 2:
        reliability_insight = f"Lower reliability (error rate up by {error_diff:.1f}pp)"
    else:
        reliability_insight = "Comparable reliability"
    
    print(f"\nKey Findings:")
    print(f"  • {cost_insight}")
    print(f"  • {quality_insight}")
    print(f"  • {latency_insight}")
    print(f"  • {reliability_insight}")
    
    # ===== PART 3B: ASK LLM FOR COMPREHENSIVE SYNTHESIS =====
    print(f"\nGenerating comprehensive insights using Claude...")
    
    # Prepare detailed metrics for Claude synthesis
    metrics_summary = f"""
EVALUATION METRICS SUMMARY:

Performance Metrics:
- Original Model Avg Latency: {avg_original_latency:.4f}s
- GPT-4o Avg Latency: {avg_gpt4o_latency:.4f}s
- Latency Change: {latency_change_pct:+.2f}%

- Original Model Avg Cost: ${avg_original_cost:.6f}
- GPT-4o Avg Cost: ${avg_gpt4o_cost:.6f}
- Cost Change: {cost_change_pct:+.2f}%

- Original Model Success Rate: {100-orig_error_rate:.2f}% ({orig_success_count}/{len(input_data)} successful)
- GPT-4o Success Rate: {100-gpt4o_error_rate:.2f}% ({gpt4o_success_count}/{len(gpt4o_data)} successful)
- Reliability Change: {error_diff:+.2f} percentage points

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

Generate ONE-LINE summary only:
"Switching to GPT-4o [COST_IMPACT] cost by X% with [QUALITY_IMPACT] quality (X/10) and [RELIABILITY_IMPACT]."

Use actual numbers from metrics above. No other text.
"""
        
        synthesis_response = portkey.chat.completions.create(
            model="@anthropic/claude-sonnet-4-5-20250929",
            messages=[
                {
                    "role": "system",
                    "content": "Generate only the one-line summary. No explanations."
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
        # Fallback to rule-based recommendation
        if cost_change_pct < 0 and overall_quality >= 7:
            comprehensive_statement = f"Switching to GPT-4o reduces cost by {abs(cost_change_pct):.1f}% while maintaining strong quality ({overall_quality:.1f}/10). This is a favorable trade-off."
        elif cost_change_pct > 0 and overall_quality > 8:
            comprehensive_statement = f"While GPT-4o increases cost by {cost_change_pct:.1f}%, it delivers superior quality ({overall_quality:.1f}/10), making it suitable for quality-critical applications."
        elif gpt4o_error_rate < orig_error_rate:
            comprehensive_statement = f"GPT-4o provides better reliability ({100-gpt4o_error_rate:.1f}% vs {100-orig_error_rate:.1f}% success rate) with quality score of {overall_quality:.1f}/10."
        else:
            comprehensive_statement = f"GPT-4o achieves a quality score of {overall_quality:.1f}/10 with cost {'reduction' if cost_change_pct < 0 else 'increase'} of {abs(cost_change_pct):.1f}%."
        print(f"\nComprehensive Statement: {comprehensive_statement}")
    
    print("\n" + "="*80)
    print("EVALUATION COMPLETE")
    print("="*80 + "\n")

# Main execution
if __name__ == "__main__":
    # Read the dataset
    input_csv = "1k_data_with_tokens_latency_cost.csv"
    
    rows_data = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows_data = list(reader)
    
    print(f"Found {len(rows_data)} questions to process")
    
    # Limit to 40 records
    rows_data = rows_data[:40]
    print(f"Processing first {len(rows_data)} records\n")
    
    # Call the function with provider, model, and costs
    # OpenAI GPT-4o pricing: $5 per 1M input tokens, $15 per 1M output tokens
    # process_questions(
    #     data=rows_data,
    #     provider="openai",
    #     model="gpt-4o",
    #     input_cost=0.000005,  # $5 / 1M tokens = $0.000005 per token
    #     output_cost=0.000015,  # $15 / 1M tokens = $0.000015 per token
    #     output_csv="gpt4o_responses.csv"
    # )
    
    # Run evaluation
    print("\n\nStarting evaluation of responses...")
    evaluate_responses(
        input_csv="1k_data_with_tokens_latency_cost.csv",
        gpt4o_csv="gpt4o_responses.csv",
        evaluation_output="evaluation_report.csv"
    )

