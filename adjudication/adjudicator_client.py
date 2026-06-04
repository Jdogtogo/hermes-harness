import json
import os
import argparse
from pydantic import BaseModel, ValidationError, field_validator
from typing import List, Literal, Optional

class AdjudicationResponse(BaseModel):
    decision: Literal["approved", "rejected", "revise", "stop"]
    phase: str
    maturity_classification: str
    blocking_issues: List[str]
    accepted_items: List[str]
    required_next_action: str
    next_instruction_for_hermes: str
    should_continue: bool

    @field_validator('should_continue')
    @classmethod
    def should_continue_only_if_approved(cls, v: str, info):
        if v and info.data.get('decision') != 'approved':
            raise ValueError('should_continue cannot be true unless decision is approved')
        return v

def validate_response(data: dict) -> AdjudicationResponse:
    return AdjudicationResponse(**data)

def adjudicate(request_path: str, response_path: str, live_mode: bool = False):
    with open(request_path, 'r') as f:
        request = json.load(f)
    
    if live_mode:
        # For now, we'll simulate a live call by using the same mock data,
        # but we'll note that we hit the live mode branch.
        # In the future, this branch would actually call the configured approval provider.
        response_data = {
            "decision": "approved",
            "phase": request.get("phase", "unknown"),
            "maturity_classification": "v1-foundation",
            "blocking_issues": [],
            "accepted_items": ["guardrail-v1", "dry-run-adjudication"],
            "required_next_action": "awaiting manual trigger",
            "next_instruction_for_hermes": "Proceed to next phase when ready",
            "should_continue": False
        }
    else:
        response_data = {
            "decision": "approved",
            "phase": request.get("phase", "unknown"),
            "maturity_classification": "v1-foundation",
            "blocking_issues": [],
            "accepted_items": ["guardrail-v1", "dry-run-adjudication"],
            "required_next_action": "awaiting manual trigger",
            "next_instruction_for_hermes": "Proceed to next phase when ready",
            "should_continue": False
        }
        
    validated = validate_response(response_data)
    with open(response_path, 'w') as f:
        f.write(validated.model_dump_json(indent=2))
    return validated

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--request", required=True)
    args = parser.parse_args()
    
    adjudicate(args.request, "/home/jfroh/hermes/harness/adjudication/live_extracted_response.json", live_mode=args.live)
