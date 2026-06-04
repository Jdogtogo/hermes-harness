import json
import os
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

def adjudicate(request_path: str, response_path: str, mock_mode: bool = True):
    with open(request_path, 'r') as f:
        request = json.load(f)
    
    if mock_mode:
        response_data = {
            "decision": "approved",
            "phase": request.get("phase", "unknown"),
            "maturity_classification": "v1-foundation",
            "blocking_issues": [],
            "accepted_items": ["guardrail-v1"],
            "required_next_action": "awaiting manual trigger",
            "next_instruction_for_hermes": "Proceed to next phase when ready",
            "should_continue": False
        }
    else:
        # Placeholder for real ChatGPT 5.5 integration
        raise NotImplementedError("Real ChatGPT 5.5 integration not yet wired")
        
    validated = validate_response(response_data)
    with open(response_path, 'w') as f:
        f.write(validated.model_dump_json(indent=2))
    return validated
