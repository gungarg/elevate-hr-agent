"""Validates OKF (Open Knowledge Format) concept files for schema correctness."""

import sys
from pathlib import Path
import yaml

def validate_bundle(bundle_path: Path) -> bool:
    print(f"Validating OKF bundle at: {bundle_path.resolve()}")
    all_valid = True
    concept_count = 0
    
    for md_file in bundle_path.glob("**/*.md"):
        rel_path = md_file.relative_to(bundle_path)
        if md_file.name in ["index.md", "log.md"]:
            continue
            
        try:
            content = md_file.read_text(encoding="utf-8")
            if not content.startswith("---"):
                print(f"[FAIL] Missing YAML frontmatter: {rel_path}")
                all_valid = False
                continue
                
            parts = content.split("---", 2)
            if len(parts) < 3:
                print(f"[FAIL] Malformed frontmatter delimiter: {rel_path}")
                all_valid = False
                continue
                
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
            
            # Check required keys
            required_keys = ["title", "description", "tags", "status", "sources"]
            missing_keys = [k for k in required_keys if k not in frontmatter]
            if missing_keys:
                print(f"[FAIL] {rel_path}: Missing required keys: {missing_keys}")
                all_valid = False
                continue
                
            if len(body) < 20:
                print(f"[WARN] {rel_path}: Body seems too short ({len(body)} chars)")
                
            concept_count += 1
            print(f"[PASS] {rel_path} (Title: {frontmatter['title']})")
            
        except Exception as e:
            print(f"[ERROR] {rel_path}: Exception while parsing: {e}")
            all_valid = False
            
    print(f"\nSummary: Validated {concept_count} concept files. All valid: {all_valid}")
    return all_valid

if __name__ == "__main__":
    bundle_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    success = validate_bundle(bundle_dir)
    sys.exit(0 if success else 1)
