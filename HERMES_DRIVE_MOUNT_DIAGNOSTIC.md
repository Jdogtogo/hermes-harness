# Hermes Drive Mount Diagnostic

## Executive Summary
The Google Drive mount point /mnt/h is mounted via drvfs (Windows H: drive) but appears intermittently inaccessible, showing "No such device" when accessed. However, session logs indicate that the My Drive directory is present under /mnt/h. The Hermes Nightly Audit script expects the path /mnt/h/My Drive/Hermes_Workspace/ for exports, backups, and master file regeneration. While the mount is configured, the full workspace path may not be available or may require manual intervention to ensure the Hermes_Workspace directory exists and is accessible.

## Starting Git Status
## harness-v1-dashboard
?? HERMES_NIGHTLY_AUDIT_TARGETED_VERIFICATION.md

## Current Mount Evidence
Mount output:
```
drivers on /usr/lib/wsl/drivers type 9p (ro,nosuid,nodev,noatime,aname=drivers;fmask=222;dmask=222,cache=5,access=client,msize=65536,trans=fd,rfd=8,wfd=8)
C:\ on /mnt/c type 9p (rw,noatime,aname=drvfs;path=C:\;uid=1000;gid=1000;symlinkroot=/mnt/,cache=5,access=client,msize=65536,trans=fd,rfd=6,wfd=6)
H: on /mnt/h type 9p (rw,relatime,aname=drvfs;path=H:;symlinkroot=/mnt/,cache=5,access=client,msize=65536,trans=fd,rfd=3,wfd=3)
```

df -h output:
```
df: /mnt/h: No such device
drivers         475G  392G   83G  83% /usr/lib/wsl/drivers
C:\             475G  392G   83G  83% /mnt/c
```

## /mnt Directory Evidence
```
ls: cannot access '/mnt/h': No such device
total 8
drwxr-xr-x  6 root  root  4096 May 31 17:13 .
drwxr-xr-x 22 root  root  4096 Jun  4 07:54 ..
drwxrwxrwx  1 jfroh jfroh  512 Jun  6 08:58 c
d?????????  ? ?     ?        ?            ? h
drwxrwxrwt  2 root  root    60 Jun  4 07:54 wsl
drwxrwxrwt  7 root  root   300 Jun  4 07:54 wslg
```

## Hermes_Workspace Search Results
The find command for Hermes_Workspace directories was interrupted (timeout). However, prior session logs from the ops profile show that executing `ls /mnt/h/` yielded:
```
$RECYCLE.BIN
My Drive
```
indicating that the My Drive directory is present under /mnt/h when the mount is accessible.

## Nightly Audit Drive Path Evidence
From /home/jfroh/.hermes/scripts/nightly_brain_audit.sh:
- Line 15: DRIVE_TARGET="/mnt/h/My Drive/Hermes_Workspace/Brain"
- Line 16: NOTEBOOK_DIR="/mnt/h/My Drive/Hermes_Workspace/Idea_Diary"
- Line 35: Error log if Google Drive mount not found at $DRIVE_TARGET
- Line 39: mkdir -p for EXPORT_DIR, DRIVE_TARGET, NOTEBOOK_DIR, log directory
- Line 51: cp "$BRAIN_DB" "${DRIVE_TARGET}/brain.sqlite"
- Line 65: mv "${EXPORT_DIR}/2_states_master.txt.tmp" "/mnt/h/My Drive/Hermes_Workspace/Setup/2_states_master.txt"
- Line 69: mv "${EXPORT_DIR}/3_runbooks_master.txt.tmp" "/mnt/h/My Drive/Hermes_Workspace/Setup/3_runbooks_master.txt"
- Lines 79-84, 88: Operations involving /mnt/h/My Drive/Hermes_Workspace/Setup/ and /mnt/h/My Drive/Hermes_Workspace/Idea_Diary/

## Shell/Profile Reference Evidence
Grep of shell configs and Hermes directories revealed no direct exports or references to /mnt/h or Hermes_Workspace in active shell rc files. Multiple references appear in session dump JSON files (e.g., request_dump_*.json) describing the Google Drive folder ID parameter, indicating that the Google Drive integration is used via the MCP tooling but not hardcoded in shell profiles.

## Diagnosis
The /mnt/h mount point is configured as a drvfs mount of the Windows H: drive. The intermittent "No such device" errors when accessing /mnt/h suggest that the underlying H: drive may be disconnected, unavailable, or the Windows side network drive (Google Drive) may not be mounted at the time of access. However, when the mount is accessible, the My Drive directory is present (as seen in ops logs). The Nightly Audit script's pre-flight check fails if the DRIVE_TARGET directory is missing, which would occur if the mount is not accessible or if the My Drive/Hermes_Workspace/Brain path does not exist.

Given that the mount shows as present in the mount table but df reports "No such device", the issue is likely that the Windows H: drive is not currently mapped or accessible from WSL, possibly due to network drive reconnection delays or permissions.

## Confirmed Facts
- The /mnt/h mount point exists in the mount table as a drvfs mount of H:.
- The Nightly Audit script correctly references the expected Google Drive workspace paths.
- When accessible, the My Drive directory is present under /mnt/h.
- The harness repository is on branch harness-v1-dashboard with only the Nightly Audit verification report untracked.

## Not Confirmed
- Whether the H: drive is currently accessible and mapped to Google Drive.
- Whether the full path /mnt/h/My Drive/Hermes_Workspace/ exists and contains the required subdirectories (Setup/, Live_Logs/, Brain/, Idea_Diary/).
- Whether the Nightly Audit script can run to completion and perform exports, backups, and master file regeneration.
- The freshness of Drive exports (Live Logs, master files, brain.sqlite backup).

## Recommended Next Actions
1. Manually verify access to /mnt/h and list its contents to confirm if My Drive is present.
2. If accessible, check for the Hermes_Workspace directory and its subdirectories.
3. If the Hermes_Workspace directory is missing, create it (or ensure the Nightly Audit script's mkdir -p succeeds).
4. Test the Nightly Audit script in a controlled manner (e.g., with a dry-run or by verifying pre-flight checks pass) to see if it can complete.
5. If the mount is persistently inaccessible, investigate the Windows H: drive mapping and Google Drive drive letter assignment.
6. Ensure that the mount is stable and available before relying on automated exports.

## Human Approval Required
Yes. Justin must verify the Drive mount availability and approve any changes or automation related to the Nightly Audit exports.
