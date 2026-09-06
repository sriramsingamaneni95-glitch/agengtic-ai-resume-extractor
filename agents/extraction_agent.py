import json
from pydantic import ValidationError

from llm_client import get_client
from schema import ResumeData
from tools.email_validator import validate_email
from tools.date_parser import parse_date
from tools.skill_normalizer import normalize_skill
from utils.retry import clean_json_text, retry_on_failure
from utils.logging_config import logger, log_call, log_token_usage

SYSTEM_PROMPT = """You are a resume extraction agent. Extract structured data
matching this JSON shape:
{
  "name": str, "email": str, "phone": str, "summary": str,
  "skills": [str],
  "experience": [{"company","title","start_date","end_date","description"}],
  "education": [{"institution","degree","year"}],
  "confidence_scores": {"name":0-1,"email":0-1,"phone":0-1,"skills":0-1,"experience":0-1,"education":0-1}
}
While extracting, USE THE PROVIDED TOOLS to validate the email you find,
normalize every date you find, and normalize every skill name you find.
Once you are done calling tools, respond with ONLY the final JSON object —
no prose, no markdown fences.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "validate_email",
            "description": "Validate and clean an email address found in the resume.",
            "parameters": {
                "type": "object",
                "properties": {"email": {"type": "string"}},
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "parse_date",
            "description": "Normalize a messy date like 'Jan 2020' or 'Present' into YYYY-MM or 'present'.",
            "parameters": {
                "type": "object",
                "properties": {"date_str": {"type": "string"}},
                "required": ["date_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "normalize_skill",
            "description": "Normalize a skill name to its canonical form (e.g. 'js' -> 'JavaScript').",
            "parameters": {
                "type": "object",
                "properties": {"skill": {"type": "string"}},
                "required": ["skill"],
            },
        },
    },
]


def _run_tool(name: str, args: dict) -> dict:
    if name == "validate_email":
        ok, cleaned = validate_email(args["email"])
        return {"valid": ok, "cleaned": cleaned}
    if name == "parse_date":
        return {"normalized": parse_date(args["date_str"])}
    if name == "normalize_skill":
        return {"normalized": normalize_skill(args["skill"])}
    return {"error": f"unknown tool {name}"}


def _assistant_message_as_dict(msg) -> dict:
    """
    BUG FIX: the OpenAI SDK's response message is a pydantic object.
    Appending it directly to `messages` and sending it back in the next
    API call is unreliable across SDK versions (tool_calls sub-objects
    don't always serialize the way the API expects). Building the dict
    explicitly guarantees the follow-up call is well-formed.
    """
    result = {"role": "assistant", "content": msg.content}
    if msg.tool_calls:
        result["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ]
    return result


@log_call
@retry_on_failure(max_attempts=3)
def extract_resume_json(resume_text: str, plan: dict) -> ResumeData:
    client = get_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context/plan: {json.dumps(plan)}\n\nResume:\n{resume_text}"},
    ]

    final_content = None
    for round_num in range(6):  # allow several tool round-trips before giving up
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        log_token_usage(response, label=f"extraction_round_{round_num}")
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(_assistant_message_as_dict(msg))
            for tool_call in msg.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = _run_tool(tool_call.function.name, args)
                logger.info(f"Tool called by model: {tool_call.function.name}({args}) -> {result}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })
            continue  # let the model see tool results and continue

        final_content = msg.content
        break

    if final_content is None:
        raise RuntimeError("Extraction agent did not converge after tool-calling rounds")

    raw_output = clean_json_text(final_content)
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON: {e}\nRaw: {raw_output}")

    try:
        return ResumeData(**data)
    except ValidationError as e:
        logger.error(f"Schema validation failed: {e}")
        raise
