# Hermes Nightly Audit Targeted Verification

## Executive Summary
Targeted verification of Nightly Brain Audit, master file regeneration, and Drive export freshness was performed. The Google Drive workspace at /mnt/h/My Drive/Hermes_Workspace/ is not accessible (device not found), preventing verification of Drive-based artifacts. Local evidence shows the nightly audit script exists and is executable, and the brain.sqlite database is present. However, without Drive access, we cannot confirm that exports, backups, or master files are being written to the Drive.

## Prior Verification Gap
Prior GoogleLM claims verification did not confirm Nightly Brain Audit or master-file regeneration, potentially due to searching broad/wrong locations. This verification targets the known Hermes Workspace Drive paths and local script/database.

## Starting Git Status
## harness-v1-dashboard
(working tree clean)

## Drive Workspace Directory Evidence
Path: /mnt/h/My Drive/Hermes_Workspace/
ls: cannot access '/mnt/h/My Drive/Hermes_Workspace/': No such device
ERROR: Cannot access /mnt/h/My Drive/Hermes_Workspace/ - No such device or directory

## Master File Timestamp Evidence
=== /mnt/h/My Drive/Hermes_Workspace/Setup/2_states_master.txt ===
stat: cannot statx '/mnt/h/My Drive/Hermes_Workspace/Setup/2_states_master.txt': No such device
STAT FAILED: /mnt/h/My Drive/Hermes_Workspace/Setup/2_states_master.txt
sed: can't read /mnt/h/My Drive/Hermes_Workspace/Setup/2_states_master.txt: No such device
SED FAILED: /mnt/h/My Drive/Hermes_Workspace/Setup/2_states_master.txt
=== /mnt/h/My Drive/Hermes_Workspace/Setup/3_runbooks_master.txt ===
stat: cannot statx '/mnt/h/My Drive/Hermes_Workspace/Setup/3_runbooks_master.txt': No such device
STAT FAILED: /mnt/h/My Drive/Hermes_Workspace/Setup/3_runbooks_master.txt
sed: can't read /mnt/h/My Drive/Hermes_Workspace/Setup/3_runbooks_master.txt: No such device
SED FAILED: /mnt/h/My Drive/Hermes_Workspace/Setup/3_runbooks_master.txt

## Master File Header Evidence
(Same as above - files not accessible)

## Live Logs Export Evidence
=== /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Live_Status.txt ===
stat: cannot statx '/mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Live_Status.txt': No such device
STAT FAILED: /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Live_Status.txt
sed: can't read /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Live_Status.txt: No such device
SED FAILED: /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Live_Status.txt
=== /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Event_Log_Rolling.txt ===
stat: cannot statx '/mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Event_Log_Rolling.txt': No such device
STAT FAILED: /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Event_Log_Rolling.txt
sed: can't read /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Event_Log_Rolling.txt: No such device
SED FAILED: /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Event_Log_Rolling.txt
=== /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Adjudication_History.txt ===
stat: cannot statx '/mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Adjudication_History.txt': No such device
STAT FAILED: /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Adjudication_History.txt
sed: can't read /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Adjudication_History.txt: No such device
SED FAILED: /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Adjudication_History.txt
=== /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Blockers_And_Human_Actions.txt ===
stat: cannot statx '/mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Blockers_And_Human_Actions.txt': No such device
STAT FAILED: /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Blockers_And_Human_Actions.txt
sed: can't read /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Blockers_And_Human_Actions.txt: No such device
SED FAILED: /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Blockers_And_Human_Actions.txt
=== /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Current_Infrastructure_State.txt ===
stat: cannot statx '/mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Current_Infrastructure_State.txt': No such device
STAT FAILED: /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Current_Infrastructure_State.txt
sed: can't read /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Current_Infrastructure_State.txt: No such device
SED FAILED: /mnt/h/My Drive/Hermes_Workspace/Live_Logs/Hermes_Current_Infrastructure_State.txt

## Nightly Audit Script Evidence
  File: /home/jfroh/.hermes/scripts/nightly_brain_audit.sh
  Size: 4043      Blocks: 8          IO Block: 4096   regular file
Device: 8,48	Inode: 109419      Links: 1
Access: (0755/-rwxr-xr-x)  Uid: ( 1000/   jfroh)   Gid: ( 1000/   jfroh)
Access: 2026-06-05 20:20:24.343653108 +1000
Modify: 2026-06-05 20:20:24.215652257 +1000
Change: 2026-06-05 20:20:24.215652257 +1000
 Birth: 2026-06-01 22:54:37.459565264 +1000
#!/usr/bin/env bash
#===============================================================================
# nightly_brain_audit.sh
#
# Exports all projects from brain.sqlite as Markdown, then securely backs up
# the database + reports to the Google Drive workspace using additive copy only.
#
# Schedule: 0 2 * * * (2:00 AM daily)
#===============================================================================
set -euo pipefail

# --- Configuration ---
BRAIN_DB="$HOME/.hermes/brain.sqlite"
EXPORT_BASE="$HOME/.hermes/brain_exports"
DRIVE_TARGET="/mnt/h/My Drive/Hermes_Workspace/Brain"
NOTEBOOK_DIR="/mnt/h/My Drive/Hermes_Workspace/Idea_Diary"
TIMESTAMP="$(date +%Y-%m-%d_%H%M%S)"
EXPORT_DIR="${EXPORT_BASE}/${TIMESTAMP}"
LOG_FILE="$HOME/.hermes/logs/nightly_brain_audit.log"

# --- Helpers ---
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

# --- Pre-flight checks ---
if [ ! -f "$BRAIN_DB" ]; then
    log "ERROR: brain.sqlite not found at $BRAIN_DB"
    exit 1
fi

if [ ! -d "$DRIVE_TARGET" ]; then
    log "ERROR: Google Drive mount not found at $DRIVE_TARGET"
    exit 1
fi

mkdir -p "$EXPORT_DIR" "$DRIVE_TARGET" "$NOTEBOOK_DIR" "$(dirname "$LOG_FILE")"

log "=== Nightly Brain Audit Started ==="

# --- Export Engine with Python Path Fix ---
log "Exporting projects from brain.sqlite... "
python3 /home/jfroh/.hermes/hermes-memory/cli/main.py export --project "Personal OS" --output "$EXPORT_DIR/Personal_OS.md" >> "$LOG_FILE" 2>&1
python3 /home/jfroh/.hermes/hermes-memory/cli/main.py export --project "debug" --output "$EXPORT_DIR/debug.md" >> "$LOG_FILE" 2>&1
python3 /home/jfroh/.hermes/hermes-memory/cli/main.py export --project "proper-test" --output "$EXPORT_DIR/proper-test.md" >> "$LOG_FILE" 2>&1

# --- Sync Sequences ---
log "Backing up brain.sqlite to Drive... "
cp "$BRAIN_DB" "${DRIVE_TARGET}/brain.sqlite"
log "[OK] brain.sqlite copied to Drive"

# --- Regenerate Master Files for NotebookLM ---
log "Regenerating master files for NotebookLM ingestion... "
if [ -f "${EXPORT_DIR}/Personal_OS.md" ]; then
    # Header for master files
    printf "# Hermes Master State Source\nGenerated: $(date '+%Y-%m-%d %H:%M:%S')\nSource: nightly_brain_audit.sh\nPurpose: NotebookLM / Gemini source context\n\n" > "${EXPORT_DIR}/2_states_master.txt.tmp"
    cat "${EXPORT_DIR}/Personal_OS.md" >> "${EXPORT_DIR}/2_states_master.txt.tmp"
    
    printf "# Hermes Master Runbooks Source\nGenerated: $(date '+%Y-%m-%d %H:%M:%S')\nSource: nightly_brain_audit.sh\nPurpose: NotebookLM / Gemini source context\n\n" > "${EXPORT_DIR}/3_runbooks_master.txt.tmp"
    cat "${EXPORT_DIR}/Personal_OS.md" "${EXPORT_DIR}/debug.md" "${EXPORT_DIR}/proper-test.md" >> "${EXPORT_DIR}/3_runbooks_master.txt.tmp"
    
    if [ -f "${EXPORT_DIR}/2_states_master.txt.tmp" ]; then
        mv "${EXPORT_DIR}/2_states_master.txt.tmp" "/mnt/h/My Drive/Hermes_Workspace/Setup/2_states_master.txt"
        log "[OK] 2_states_master.txt regenerated"
    fi
    if [ -f "${EXPORT_DIR}/3_runbooks_master.txt.tmp" ]; then
        mv "${EXPORT_DIR}/3_runbooks_master.txt.tmp" "/mnt/h/My Drive/Hermes_Workspace/Setup/3_runbooks_master.txt"
        log "[OK] 3_runbooks_master.txt regenerated"
    fi
else
    log "[WARN] Personal_OS.md not found in export; skipping master file regeneration"
fi

# --- NotebookLM Context Ingestion Layer ---
log "Compiling clean text mirror for NotebookLM ingestion... "
if [ -f "${EXPORT_DIR}/Personal_OS.md" ]; then
    cat "/mnt/h/My Drive/Hermes_Workspace/Setup/3_runbooks_master.txt" \
        "${EXPORT_DIR}/Personal_OS.md" \
        > "${NOTEBOOK_DIR}/system_context_mirror.txt" 2>>"$LOG_FILE"
else
    # Fallback to last known file if active export layout is shifting
    cat "/mnt/h/My Drive/Hermes_Workspace/Setup/3_runbooks_master.txt" \
        "${DRIVE_TARGET}/Personal_OS.md" \
        > "${NOTEBOOK_DIR}/system_context_mirror.txt" 2>>"$LOG_FILE" 2>/dev/null || true
fi
log "[OK] Plain text snapshot synchronized to Drive"

log "=== Nightly Brain Audit Complete ==="

## Recent Audit/Log Evidence
2026-05-31 20:09 /home/jfroh/.hermes/kanban/boards/fund-manager-intelligence/logs/t_1637a763.log
2026-05-31 20:09 /home/jfroh/.hermes/profiles/backend-eng/logs/agent.log
2026-06-03 20:53 /home/jfroh/.hermes/skills/autonomous-ai-agents/hermes-agent-audit/references/litellm-config-audit.md
2026-06-03 22:20 /home/jfroh/.hermes/interrupt_debug.log
2026-06-04 07:01 /home/jfroh/.hermes/skills/.hub/audit.log
2026-06-04 10:44 /home/jfroh/.hermes/hermes-agent/venv/lib/python3.11/site-packages/discord/__pycache__/audit_logs.cpython-311.pyc
2026-06-04 17:53 /home/jfroh/.hermes/profiles/thinker/logs/errors.log
2026-06-04 17:54 /home/jfroh/.hermes/kanban/boards/fund-manager-intelligence/logs/t_e5f434e4.log
2026-06-04 17:54 /home/jfroh/.hermes/profiles/thinker/logs/agent.log
2026-06-05 18:44 /home/jfroh/.hermes/scripts/nightly_brain_audit.sh.bak_20260605_184432
2026-06-05 18:44 /home/jfroh/.hermes/scripts/nightly_brain_audit.sh.bak_20260605_184457
2026-06-05 18:45 /home/jfroh/.hermes/scripts/nightly_brain_audit.sh.backup_before_fix_20260605_184509
2026-06-05 19:42 /home/jfroh/.hermes/disk-cleanup/cleanup.log
2026-06-05 20:19 /home/jfroh/.hermes/scripts/nightly_brain_audit.sh.bak_20260605_201902
2026-06-05 20:20 /home/jfroh/.hermes/scripts/nightly_brain_audit.sh
2026-06-06 01:55 /home/jfroh/.hermes/cron/output/sync_flush.log
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/cjs/internal/operators/audit.js
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/cjs/internal/operators/audit.js.map
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/cjs/internal/operators/auditTime.js
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/cjs/internal/operators/auditTime.js.map
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/esm/internal/operators/audit.js
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/esm/internal/operators/audit.js.map
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/esm/internal/operators/auditTime.js
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/esm/internal/operators/auditTime.js.map
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/esm5/internal/operators/audit.js
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/esm5/internal/operators/audit.js.map
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/esm5/internal/operators/auditTime.js
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/esm5/internal/operators/auditTime.js.map
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/types/internal/operators/audit.d.ts
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/types/internal/operators/auditTime.d.ts
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/dist/types/internal/operators/auditTime.d.ts.map
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/src/internal/operators/audit.ts
2026-06-06 08:38 /home/jfroh/.hermes/hermes-agent/node_modules/rxjs/src/internal/operators/auditTime.ts
2026-06-06 09:46 /home/jfroh/.hermes/logs/mcp-stderr.log
2026-06-06 09:51 /home/jfroh/.hermes/logs/update.log
2026-06-06 10:00 /home/jfroh/.hermes/logs/gmail_intake_v2.log
2026-06-06 10:01 /home/jfroh/.hermes/logs/gateway.log
2026-06-06 10:04 /home/jfroh/.hermes/logs/agent.log
2026-06-06 10:04 /home/jfroh/.hermes/logs/errors.log

## brain.sqlite Local Evidence
  File: /home/jfroh/.hermes/brain.sqlite
  Size: 98304     Blocks: 192        IO Block: 4096   regular file
Device: 8,48	Inode: 847466      Links: 1
Access: (0644/-rw-r--r--)  Uid: ( 1000/   jfroh)   Gid: ( 1000/   jfroh)
Access: 2026-06-06 02:00:01.466973565 +1000
Modify: 2026-06-01 20:39:24.863895755 +1000
Change: 2026-06-01 20:39:24.863895755 +1000
 Birth: 2026-05-31 13:30:46.852394067 +1000

## brain.sqlite Drive Backup Evidence
Drive not accessible; cannot verify backup.

## Confirmed Claims
- The nightly audit script exists at /home/jfroh/.hermes/scripts/nightly_brain_audit.sh and is executable.
- The brain.sqlite database exists at /home/jfroh/.hermes/brain.sqlite.
- The script attempts to export projects and back up the database to the Drive workspace.

## Not Confirmed Claims
- Drive workspace accessibility (/mnt/h/My Drive/Hermes_Workspace/).
- Master file generation and timestamps in Drive.
- Live Logs export files in Drive.
- Actual backup of brain.sqlite to Drive.
- Regeneration of master files for NotebookLM.
- Plain text snapshot synchronization to Drive.

## Risks
- The Google Drive workspace is not mounted or accessible, causing the nightly audit script to fail at the pre-flight check (if run) due to missing DRIVE_TARGET directory.
- Without Drive access, the audit cannot complete its intended functions of exporting, backing up, and generating master files.
- Local exports may still occur in $HOME/.hermes/brain_exports, but the Drive synchronization and master file regeneration for NotebookLM will not succeed.

## Recommended Next Actions
1. Verify and fix the Google Drive mount at /mnt/h/My Drive/Hermes_Workspace/.
2. Ensure the Drive workspace directories exist: Setup/, Live_Logs/, Brain/, Idea_Diary/.
3. After restoring Drive access, run the nightly audit script manually to verify it completes successfully.
4. Check the generated files in the Drive workspace for correct timestamps and content.
5. Monitor the logs at $HOME/.hermes/logs/nightly_brain_audit.log for any errors.

## Human Approval Required
Yes. Justin must verify the Drive mount and approve any further automation or changes to the nightly audit process.