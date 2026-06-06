# WSL H Drive Troubleshooting Runbook

## Purpose

This runbook documents how to diagnose and resolve a stale or broken WSL drvfs mount for the Windows H: drive (Google Drive File Stream / "My Drive") at `/mnt/h` inside WSL. A stale mount prevents Hermes Nightly Brain Audit and other Drive-dependent workflows from reading or writing Google Drive files.

## When This Runbook Applies

Use this runbook when:
- Hermes Nightly Brain Audit fails to update files under `/mnt/h/My Drive/Hermes_Workspace/`
- Any WSL process reports "No such device" for `/mnt/h`
- `ls /mnt` shows `h` with corrupted permissions (e.g., `d?????????`)
- `df -h /mnt/h` reports "No such device"
- Windows File Explorer and cmd.exe can access H: normally, but WSL cannot

## Known Good Path

```
/mnt/h/My Drive/Hermes_Workspace/
```

When the mount is healthy, this path is accessible and contains:
- `Brain/brain.sqlite`
- `Setup/2_states_master.txt`
- `Setup/3_runbooks_master.txt`
- `Idea_Diary/system_context_mirror.txt`

## Symptoms of Broken /mnt/h

| Symptom | Command | Expected broken output |
|---|---|---|
| No such device | `df -h /mnt/h` | `/mnt/h: No such device` |
| Cannot access | `ls -ld /mnt/h` | `cannot access '/mnt/h': No such device` |
| Corrupted directory entry | `ls -la /mnt` | `h` shown as `d?????????` |
| Cannot list contents | `ls -la "/mnt/h/My Drive/Hermes_Workspace/"` | `No such file or directory` or `No such device` |

## Safe Diagnostic Commands

Run these commands in order to confirm the mount state. All are read-only and safe.

```bash
# 1. Confirm harness repo context
cd /home/jfroh/hermes/harness && git status --short --branch

# 2. Check if the Hermes_Workspace path is accessible
ls -la "/mnt/h/My Drive/Hermes_Workspace/" 2>&1 || true

# 3. Check df for /mnt/h
df -h /mnt/h 2>&1 || true

# 4. Check the /mnt/h directory entry itself
ls -ld /mnt/h 2>&1 || true

# 5. List all mounts under /mnt to see if h appears corrupted
ls -la /mnt 2>&1 || true

# 6. Verify H: is accessible from Windows side (via cmd.exe)
cmd.exe /c "cd /d H: && dir \"My Drive\\Hermes_Workspace\"" 2>&1 | head -80
```

## Decision Rule

If ANY of the following are true:
- `df -h /mnt/h` returns "No such device"
- `ls -ld /mnt/h` returns "No such device"
- `ls -la /mnt` shows `h` as `d?????????`
- `ls -la "/mnt/h/My Drive/Hermes_Workspace/"` fails

THEN:
1. Stop all Drive-related work immediately.
2. Do NOT attempt to remount, unmount, or run `wsl --shutdown` from within WSL.
3. Proceed to "Instruction to Give Justin" below.

If ALL commands succeed and the path is accessible, the mount is healthy. Proceed with normal Drive-dependent work.

## Instruction to Give Justin

If the mount is broken, tell Justin:

> WSL /mnt/h is stale/broken (No such device). Please run `wsl --shutdown` from Windows PowerShell, then restart WSL/Hermes and recheck `/mnt/h/My Drive/Hermes_Workspace/`.

## What Hermes Must Not Do

- **NEVER** run `wsl --shutdown` from within WSL. This will terminate the running WSL session and kill the Hermes process.
- **NEVER** attempt to unmount or remount `/mnt/h` from within WSL.
- **NEVER** modify `/etc/fstab` or WSL mount configuration.
- **NEVER** create symlinks or workarounds that bypass the mount.
- **NEVER** continue Drive-dependent work (Nightly Brain Audit, Drive export, file reads/writes) while the mount is broken. Stop and escalate.

## Post-Restart Verification

After Justin runs `wsl --shutdown` from PowerShell and restarts WSL/Hermes, verify the mount is healthy:

```bash
ls -la "/mnt/h/My Drive/Hermes_Workspace/"
```

Expected output: directory listing showing Hermes_Workspace contents (Brain/, Setup/, Idea_Diary/, etc.).

If this command succeeds, the mount is restored and Drive-dependent work can resume.

## Escalation Criteria

Escalate to Justin if:
- The mount remains broken after `wsl --shutdown` and WSL restart.
- The mount breaks repeatedly (more than once per day).
- `cmd.exe /c "cd /d H: && dir"` also fails (indicates a Windows-side H: drive issue, not just WSL).
- Any data loss or file corruption is suspected in `/mnt/h/My Drive/Hermes_Workspace/`.

## One-Line Operator Summary

If /mnt/h shows "No such device" or d?????????, stop Drive-related work and ask Justin to run `wsl --shutdown` from PowerShell, then restart WSL/Hermes and recheck `/mnt/h/My Drive/Hermes_Workspace/`.
