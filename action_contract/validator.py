import yaml
import re

class ActionContractValidator:
    def __init__(self):
        self.required_fields = [
            "action_id", "workstream", "risk_class", "requested_mode",
            "working_directory", "intent", "commands", "files",
            "external_services", "git", "memory", "skills", "governance",
            "evidence_requirements", "acceptance_criteria", "forbidden_patterns",
            "rollback_plan", "kill_switch"
        ]
        self.categories = {"runner", "rag", "governance", "git", "system", "api", "research"}
        self.risk_classes = {"green", "amber", "orange", "red"}
        self.modes = {"plan", "act", "review", "dry_run", "evaluation_only"}

    def validate(self, action_dict):
        # 1. Missing required field
        for field in self.required_fields:
            if field not in action_dict:
                return "ACTION_CONTRACT_ESCALATE"

        # Structural check
        try:
            # Enums
            if action_dict["workstream"].get("category") not in self.categories:
                return "ACTION_CONTRACT_ESCALATE"
            if action_dict["risk_class"] not in self.risk_classes:
                return "ACTION_CONTRACT_ESCALATE"
            if action_dict["requested_mode"] not in self.modes:
                return "ACTION_CONTRACT_ESCALATE"
            if not action_dict["action_id"] or not action_dict["working_directory"]:
                return "ACTION_CONTRACT_ESCALATE"
            if not action_dict["acceptance_criteria"] or not action_dict["forbidden_patterns"] or not action_dict["rollback_plan"]:
                return "ACTION_CONTRACT_ESCALATE"
        except:
            return "ACTION_CONTRACT_ESCALATE"

        # 2. V0 Logic
        # requested_mode act with risk_class orange or red
        if action_dict["requested_mode"] == "act" and action_dict["risk_class"] in {"orange", "red"}:
            return "ACTION_CONTRACT_INVALID"
        
        # git.allow_push true
        if action_dict["git"].get("allow_push"):
            return "ACTION_CONTRACT_INVALID"
        
        # memory.allow_write true
        if action_dict["memory"].get("allow_write"):
            return "ACTION_CONTRACT_INVALID"
            
        # skills allow
        if action_dict["skills"].get("allow_create") or action_dict["skills"].get("allow_modify"):
            return "ACTION_CONTRACT_INVALID"
            
        # governance
        if action_dict["governance"].get("allow_modify"):
            return "ACTION_CONTRACT_INVALID"
            
        # files.delete non-empty
        if action_dict["files"].get("delete"):
            return "ACTION_CONTRACT_INVALID"
            
        # external_services.enabled non-empty
        if action_dict["external_services"].get("enabled"):
            return "ACTION_CONTRACT_INVALID"
            
        # Command checks
        all_cmds = " ".join(action_dict["commands"]["allowed"])
        forbidden_patterns = ["git push", "git add .", ".env", "auth.json", "token", "secret", "password", "private_key", "rm", "rmdir", "del", "mv", "move", "chmod 777"]
        for p in forbidden_patterns:
            if p in all_cmds:
                return "ACTION_CONTRACT_INVALID"
        
        return "ACTION_CONTRACT_VALID"
