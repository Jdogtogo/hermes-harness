import pytest
import json
import os
from pydantic import ValidationError
from adjudication.adjudicator_client import validate_response

def test_valid_approved_response():
    data = {
        "decision": "approved",
        "phase": "v1",
        "maturity_classification": "alpha",
        "blocking_issues": [],
        "accepted_items": ["item1"],
        "required_next_action": "none",
        "next_instruction_for_hermes": "continue",
        "should_continue": False
    }
    assert validate_response(data).decision == "approved"

def test_valid_revise_response():
    data = {
        "decision": "revise",
        "phase": "v1",
        "maturity_classification": "alpha",
        "blocking_issues": ["issue"],
        "accepted_items": [],
        "required_next_action": "fix it",
        "next_instruction_for_hermes": "do better",
        "should_continue": False
    }
    assert validate_response(data).decision == "revise"

def test_invalid_decision_rejected():
    data = {
        "decision": "foo",
        "phase": "v1",
        "maturity_classification": "alpha",
        "blocking_issues": [],
        "accepted_items": [],
        "required_next_action": "none",
        "next_instruction_for_hermes": "none",
        "should_continue": False
    }
    with pytest.raises(ValidationError):
        validate_response(data)

def test_should_continue_true_rejected_when_decision_is_not_approved():
    data = {
        "decision": "revise",
        "phase": "v1",
        "maturity_classification": "alpha",
        "blocking_issues": [],
        "accepted_items": [],
        "required_next_action": "none",
        "next_instruction_for_hermes": "none",
        "should_continue": True
    }
    with pytest.raises(ValidationError):
        validate_response(data)

def test_missing_required_key_rejected():
    data = {
        "decision": "approved",
        "phase": "v1"
        # missing other fields
    }
    with pytest.raises(ValidationError):
        validate_response(data)
