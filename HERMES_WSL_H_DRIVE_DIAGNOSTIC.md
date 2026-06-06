# Hermes WSL H Drive Diagnostic

## Executive Summary
Windows H: drive (Google Drive) is accessible via cmd.exe and contains the expected Hermes_Workspace directory with all required subdirectories (Setup, Live_Logs, Brain, Idea_Diary) and files. However, WSL's /mnt/h mount point, while appearing in the mount table as a drvfs mount of H:, is broken: df reports "No such device", ls cannot access it, and /mnt shows the entry as d?????????. This indicates a stale or broken WSL drvfs mount, not a missing Google Drive folder. The Nightly Audit script's expected paths (/mnt/h/My Drive/Hermes_Workspace/*) are therefore inaccessible from WSL, even though they exist on the Windows side.

## Starting Git Status
## harness-v1-dashboard
?? HERMES_DRIVE_MOUNT_DIAGNOSTIC.md
?? HERMES_NIGHTLY_AUDIT_TARGETED_VERIFICATION.md

## WSL /mnt/h Evidence
Mount output:
```
H: on /mnt/h type 9p (rw,relatime,aname=drvfs;path=H:;symlinkroot=/mnt/,cache=5,access=client,msize=65536,trans=fd,rfd=3,wfd=3)
```

df -h /mnt/h output:
```
df: /mnt/h: No such device
```

ls -ld /mnt/h output:
```
ls: cannot access '/mnt/h': No such device
```

ls -la /mnt output shows:
```
d?????????  ? ?     ?        ?            ? h
```
indicating an inconsistent or broken mount entry.

## Windows H Drive Evidence via cmd.exe
- H: volume label is Google Drive, serial 1983-1116.
- Root of H: contains My Drive directory.
- H:\My Drive contains Hermes_Workspace directory (among others).

## Hermes_Workspace Evidence via cmd.exe
H:\My Drive\Hermes_Workspace contains:
- Brain/ (with brain.sqlite and reports/, shadow/)
- Setup/ (with 2_states_master.md, 3_runbooks_master.md, 2_states_master.txt, 3_runbooks_master.txt, etc.)
- Live_Logs/ (with Hermes_Live_Status.txt, Hermes_Event_Log_Rolling.txt, etc.)
- Idea_Diary/ (with system_context_mirror.txt, idea notes, research notes, etc.)
- test-proj/ (likely a test folder)

All required folders and files are present and have recent timestamps (mostly 2026-06-06 02:00 AM or similar).

## Required Folder Evidence
All required subdirectories under Hermes_Workspace are present:
- Setup: contains master files (both .md and .txt versions) and configs.
- Live_Logs: contains rolling logs and status files.
- Brain: contains brain.sqlite (98,304 bytes) and directories.
- Idea_Diary: contains system context mirror and idea notes.

## Alternative /mnt/c Google Drive Path Search
Search under /mnt/c/Users/jfroh for Google Drive, My Drive, or Hermes_Workspace directories yielded no output (likely none found or not within depth). However, the Windows H: drive is mapped separately and not necessarily under the user profile.

## WSL Automount Config Evidence
Content of /etc/wsl.conf:
```
[boot]
systemd=true

[user]
default=jfroh

[automount]
enabled = true
root = /mnt/
options = "metadata"
```

## Diagnosis
The WSL mount point /mnt/h is configured correctly in /etc/wsl.conf and shows as mounted in the mount table, but the drvfs filesystem is inaccessible (df and ls fail). This is a known WSL issue where drvfs mounts can become stale, especially if the underlying Windows drive (H:) was remounted, disconnected, or if there were network delays. The Windows H: drive itself is healthy and accessible via cmd.exe, confirming that Google Drive is mounted and the Hermes_Workspace structure is intact.

The breakage is specific to the WSL side of the mount. Since the mount options include `symlinkroot=/mnt/` and `cache=5`, there may be a symlink or caching issue. The d????????? permissions in /mnt listing further indicate that the inode or metadata for the mount point is corrupted or not readable.

Because the Nightly Audit script relies on /mnt/h/My Drive/Hermes_Workspace/ paths, it will fail its pre-flight check (missing DRIVE_TARGET) and cannot export, back up, or regenerate master files until the WSL mount is restored.

## Confirmed Facts
- Windows H: drive (Google Drive) is accessible and contains the Hermes_Workspace directory with all required subfolders and files.
- WSL mount table shows H: mounted at /mnt/h with drvfs type.
- /etc/wsl.conf has automount enabled with root /mnt/ and metadata options.
- The harness repository is on branch harness-v1-dashboard with two diagnostic reports untracked.

## Not Confirmed
- Whether restarting the WSL mount (e.g., via umount and remount) would restore access without restarting WSL or Windows.
- Whether the issue is transient due to a temporary network glitch or requires persistent fix (e.g., fixing /etc/wsl.conf or Windows drive mapping).
- Whether the Nightly Audit script would succeed if the WSL mount were restored (though local script and database are present).

## Recommended Next Actions
1. Attempt to unmount and remount /mnt/h from WSL (if permitted) to see if accessibility is restored:
   - sudo umount /mnt/h
   - sudo mount -t drvfs H: /mnt/h
2. If that fails, check for conflicting mounts or try mounting with different options (e.g., removing cache, specifying uid/gid).
3. Verify that the Windows H: drive mapping is stable and not being disconnected/reconnected frequently.
4. Consider using an alternative path: if Google Drive is also accessible via /mnt/c/Users/jfroh/... (though not found in search), or use the Windows path directly via /mnt/c/... if applicable.
5. As a workaround, modify the Nightly Audit script to use a local export path and manually copy to Drive, or use the Windows path via /mnt/c if Google Drive appears there.
6. Monitor the mount state over time to see if the issue recurs after remount.

## Human Approval Required
Yes. Justin must verify the WSL mount state and approve any changes to the mount configuration or the Nightly Audit script paths.
