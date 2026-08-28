"""Evaluation runner for HR Multi-Agent Assistant."""

import sys
import json
from pathlib import Path

# Add repository root to python path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app import process_agent_turn

EVAL_DATASET = Path(__file__).parent / "datasets" / "benchmark_golden_cases.json"

def run_eval():
    if not EVAL_DATASET.exists():
        print(f"Dataset not found at {EVAL_DATASET}")
        return
        
    with open(EVAL_DATASET, "r", encoding="utf-8") as f:
        test_cases = json.load(f)
        
    print(f"===============================================================")
    print(f"RUNNING EVALUATION SUITE ({len(test_cases)} Test Cases)")
    print(f"===============================================================\n")
    
    passed = 0
    total = len(test_cases)
    
    for idx, tc in enumerate(test_cases, 1):
        print(f"[{idx}/{total}] Running: {tc['id']} - {tc['description']}")
        print(f"Query: \"{tc['query']}\"")
        
        try:
            result = process_agent_turn(tc["query"], employee_id="gunjangarg")
            response = result.get("response", "")
            traces = result.get("traces", [])
            
            # 1. Evaluate Grounding matches
            groundings_matched = []
            for g in tc.get("expected_grounding", []):
                if g.lower() in response.lower():
                    groundings_matched.append(g)
                    
            grounding_score = len(groundings_matched) / len(tc["expected_grounding"]) if tc.get("expected_grounding") else 1.0
            
            # 2. Check section citation if applicable
            section_matched = True
            if "expected_section" in tc:
                section_matched = tc["expected_section"] in response or f"Section {tc['expected_section']}" in response
                
            # 3. Check tool execution if applicable
            tool_matched = True
            if "expected_tool" in tc:
                executed_tools = [t.get("tool", "") for t in traces]
                tool_matched = any(tc["expected_tool"] in t for t in executed_tools)
                
            is_pass = (grounding_score >= 0.5) and section_matched and tool_matched
            if is_pass:
                passed += 1
                print(f"Status: PASS (Grounding: {grounding_score:.0%}, Latency: {result.get('duration_ms', 0)}ms)\n")
            else:
                print(f"Status: FAIL (Grounding: {grounding_score:.0%}, Section: {section_matched}, Tool: {tool_matched})")
                print(f"Response snippet: {response[:180]}...\n")
                
        except Exception as e:
            print(f"Status: ERROR ({e})\n")
            
    accuracy = (passed / total) * 100
    print(f"===============================================================")
    print(f"EVALUATION SUMMARY: {passed}/{total} Passed ({accuracy:.1f}% Accuracy)")
    print(f"===============================================================")

if __name__ == "__main__":
    run_eval()
