class StatusReporter:
    def report(self, v1c_result):
        if not v1c_result or "status" not in v1c_result:
            return {"status": "CONTROL_CHAIN_V1D_STATUS_REPORT_ESCALATED"}
        
        if v1c_result["status"] != "CONTROL_CHAIN_V1C_REPO_STATUS_PASS" or v1c_result.get("returncode", 0) != 0:
            return {"status": "CONTROL_CHAIN_V1D_STATUS_REPORT_BLOCKED"}
        
        raw_stdout = v1c_result.get("stdout", "")
        
        if not raw_stdout.strip():
            return {
                "status": "CONTROL_CHAIN_V1D_STATUS_REPORT_PASS",
                "repo_dirty": False,
                "file_counts": {},
                "files_by_category": {},
                "raw_stdout": raw_stdout,
                "recommendation": "no_action",
                "safety_notes": "Parsed using local V1D logic only"
            }
        
        categories = {
            "modified": [],
            "added": [],
            "deleted": [],
            "renamed": [],
            "copied": [],
            "untracked": [],
            "unknown": []
        }
        
        for line in raw_stdout.splitlines():
            if not line.strip():
                continue
            if len(line) < 3:
                categories["unknown"].append(line)
                continue
                
            prefix = line[:2]
            filename = line[3:]
            
            if prefix == "??":
                categories["untracked"].append(filename)
            elif prefix in ["M ", " M"]:
                categories["modified"].append(filename)
            elif prefix in ["A ", " A"]:
                categories["added"].append(filename)
            elif prefix in ["D ", " D"]:
                categories["deleted"].append(filename)
            elif prefix.startswith("R"):
                categories["renamed"].append(filename)
            elif prefix.startswith("C"):
                categories["copied"].append(filename)
            else:
                categories["unknown"].append(line)
                
        file_counts = {k: len(v) for k, v in categories.items() if v}
        
        return {
            "status": "CONTROL_CHAIN_V1D_STATUS_REPORT_PASS",
            "repo_dirty": True,
            "file_counts": file_counts,
            "files_by_category": {k: v for k, v in categories.items() if v},
            "raw_stdout": raw_stdout,
            "recommendation": "review_required",
            "safety_notes": "Parsed using local V1D logic only"
        }
