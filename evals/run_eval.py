"""Evaluation runner for HR Multi-Agent Assistant."""

import sys
import json
import asyncio
from pathlib import Path
from agent.agent import run_query

EVAL_DATASET = Path(__file__).parent / "datasets" / "benchmark_golden_cases.json"

async def run_eval():
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
            response = await run_query(tc["query"])
            
            # Evaluate groundings
            groundings_matched = []
            for g in tc.get("expected_grounding", []):
                if g.lower() in response.lower():
                    groundings_matched.append(g)
                    
            grounding_score = len(groundings_matched) / len(tc["expected_grounding"]) if tc.get("expected_grounding") else 1.0
            
            # Check section citation
            section_matched = True
            if "expected_section" in tc:
                section_matched = tc["expected_section"] in response or f"Section {tc['expected_section']}" in response
                
            is_pass = (grounding_score >= 0.5) and section_matched
            if is_pass:
                passed += 1
                print(f"Status: PASS (Grounding: {grounding_score:.0%})\n")
            else:
                print(f"Status: FAIL (Grounding: {grounding_score:.0%}, Section cited: {section_matched})")
                print(f"Response snippet: {response[:200]}...\n")
                
        except Exception as e:
            print(f"Status: ERROR ({e})\n")
            
    accuracy = (passed / total) * 100
    print(f"===============================================================")
    print(f"EVALUATION SUMMARY: {passed}/{total} Passed ({accuracy:.1f}% Accuracy)")
    print(f"===============================================================")

if __name__ == "__main__":
    asyncio.run(run_eval())
