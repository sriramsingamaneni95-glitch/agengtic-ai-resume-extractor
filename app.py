
import json
from pathlib import Path
from dotenv import load_dotenv

from orchestrator import run_pipeline
from feedback import record_correction

load_dotenv()

RESUME_FILE = "sample_resume.txt"  
JD_FILE = "job_description.txt"   
OUTPUT_FILE = "output.json"


def read_text_file(path: str, label: str, required: bool = True) -> str | None:
    p = Path(path)
    if not p.exists():
        if required:
            raise FileNotFoundError(f"Could not find {label} file at '{path}'.")
        return None

    if p.suffix.lower() == ".pdf":
        from tools.pdf_parser import parse_pdf
        content = parse_pdf(str(p)).strip()
    else:
        content = p.read_text(encoding="utf-8").strip()

    if not content and required:
        raise ValueError(f"'{path}' ({label}) is empty.")
    return content or None


def run_human_feedback_loop(result: dict):
    fields = result["low_confidence_fields"]
    if not fields:
        return
    print(f"\n⚠️  Low-confidence fields need review: {fields}")
    for field_name in fields:
        current_val = result["data"].get(field_name)
        answer = input(f"  Is '{field_name}' = {current_val!r} correct? (y/n/skip): ").strip().lower()
        if answer == "n":
            corrected = input(f"  Enter corrected value for {field_name}: ").strip()
            record_correction(RESUME_FILE, field_name, current_val, corrected)
            print("  ✅ Correction saved — knowledge base/memory updated for future runs.")


def main():
    try:
        resume_text = read_text_file(RESUME_FILE, "resume")
        jd_text = read_text_file(JD_FILE, "job description", required=False)

        result = run_pipeline(resume_text, resume_name=RESUME_FILE, jd_text=jd_text)

        print(json.dumps(result, indent=2, ensure_ascii=False))
        Path(OUTPUT_FILE).write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\nSaved structured data to '{OUTPUT_FILE}'")
        print(f"Agent path taken: {' -> '.join(result['agent_trace'])}")

        run_human_feedback_loop(result)

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
