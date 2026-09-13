# AOF7 Windows Installer Kit Design

**Date:** 2026-09-11  
**Status:** Approved for implementation

## Goal

Provide a double-click Windows kit that reads a CurseForge `manifest.json`, installs the exact AOF7 2.5.3 client files, and prepares an isolated instance under the current user's `Documents` folder for the official Minecraft Launcher.

## Scope

The kit supports Windows 10/11 on x64, ARM64 through Windows x64 emulation, and Win32 when the matching Python bootstrap is available. It does not require administrator privileges, modify the system Python installation, or distribute third-party mod binaries inside the kit.

The user must own Minecraft: Java Edition and complete Microsoft sign-in in the official launcher. The kit automates files and profile setup, not Microsoft authentication.

## Inputs

The kit directory contains:

```text
AOF7-Windows-Kit/
  Install-AOF7.cmd
  Install-AOF7.ps1
  aof7_installer.py
  manifest.json
  overrides/                 optional CurseForge overrides tree
```

The manifest must be valid CurseForge format and contain `minecraft.version`, `minecraft.modLoaders`, and `files[].downloadUrl`. If a file has no direct URL, installation stops with an actionable list of missing entries; the kit never guesses a mod version.

## Output

The default output is:

```text
C:\Users\<current-user>\Documents\AOF7-2.5.3\
  mods/                     downloaded manifest files
  config/                   copied overrides
  resourcepacks/            copied overrides when present
  shaderpacks/              copied overrides when present
  tools/python/             pinned embeddable Python runtime
  logs/                     timestamped installer log
  .aof7-install-state.json  URL, filename, size, and SHA-256 state
  AOF7-2.5.3-launch.cmd     opens the official launcher after setup
```

Existing files are never silently overwritten. A rerun reuses verified files, creates a timestamped backup before replacing changed configuration, and leaves incomplete `.part` files recoverable.

## Installation flow

1. `Install-AOF7.cmd` resolves its own directory, requests a process-local PowerShell execution policy bypass, and forwards all arguments to `Install-AOF7.ps1`.
2. PowerShell checks Windows version, architecture, TLS 1.2+, writable `Documents`, and available disk space before downloading anything.
3. PowerShell selects the matching official Python 3.12.10 embeddable archive, verifies its pinned SHA-256, extracts it to `tools/python`, and enables the standard library path in `python312._pth`.
4. Python validates the manifest schema, requires Minecraft `1.20.1` and Fabric loader `0.16.0`, canonicalizes filenames, rejects path traversal, deduplicates URLs, and downloads files into `mods`.
5. Downloads use bounded parallelism, HTTP resume where supported, exponential backoff for transient failures and rate limits, atomic `.part` replacement, content-length checks, and a final SHA-256 record. Permanent failures are summarized with URL and filename.
6. Python copies `overrides` into the output with the same traversal protections and without following links outside the kit.
7. PowerShell installs the matching Fabric client profile into the official launcher game directory metadata, using the official Fabric installer and the launcher runtime when available. If no usable Java runtime or launcher installation exists, it stops before modifying the profile and explains the required action.
8. The kit writes a launcher shortcut command that opens the official launcher and records the isolated `gameDir` so the global `.minecraft` files remain untouched.
9. A final check confirms the required loader, manifest file count, mod JAR readability, override copy, output path, and launcher profile. The log records success or an actionable failure report.

## Exact versions and sources

- Modpack: All of Fabric 7 `2.5.3`.
- Minecraft: `1.20.1`.
- Fabric Loader: `0.16.0`.
- Bootstrap Python: `3.12.10` embeddable package, architecture-matched, from `python.org`.
- Official pack file: `https://mediafilez.forgecdn.net/files/6766/319/All+of+Fabric+7-2.5.3.zip`.
- Fabric installer source: `https://fabricmc.net/use/installer/`.

The kit consumes the local `manifest.json`; it does not hard-code a mod list or download a second pack manifest.

## Error handling and safety

- All external input paths and manifest filenames are resolved under their intended root and rejected if they escape it.
- Only HTTPS URLs are accepted unless an explicit `-AllowHttp` diagnostic option is supplied; the normal kit has no HTTP fallback.
- Downloads are written to `.part`, flushed, then atomically renamed. Existing valid files are kept when a replacement download fails.
- Every network request has connect/read timeouts, bounded retries, and a clear error category.
- A named mutex prevents two installers from modifying the same output concurrently.
- A backup directory is created before changing an existing launcher profile or output configuration.
- No credentials, Microsoft tokens, or Playit secrets are read or logged.
- No `pip install` or system-wide registry changes are performed.
- The kit exits nonzero on any failed required file and never reports completion with missing mods.

## Launcher integration

The official launcher remains responsible for authentication and game execution. The installer creates a named Fabric installation with:

```text
name: AOF7 2.5.3
minecraft: 1.20.1
loader: Fabric 0.16.0
gameDir: C:\Users\<current-user>\Documents\AOF7-2.5.3
```

The user opens the official launcher, selects `AOF7 2.5.3`, and clicks Play. A direct ZIP extraction into `.minecraft` is not treated as installation because CurseForge manifests do not contain the complete mod binaries.

## Testing and acceptance

Automated checks run on the repository host:

- Python syntax compilation.
- Manifest validation with the real AOF7 manifest.
- URL deduplication and filename/path traversal tests.
- Retry and resume behavior through a local HTTP test server.
- Atomic download and rerun/idempotency tests.
- Override copy tests with valid, traversal, and symlink-like inputs.
- PowerShell parse check and command-line help check when PowerShell is available.

Windows acceptance requires:

- Clean Windows 10/11 x64 run from a folder containing only the kit and manifest.
- Successful Python bootstrap without administrator elevation.
- All manifest downloads present and verified.
- Fabric profile visible in the official launcher with the isolated game directory.
- AOF7 reaches the title screen and connects to the server using the existing Playit address.
- Rerun completes without redownloading verified files or corrupting the profile.
- Forced network failure leaves the old valid file and produces a resumable log.

## Non-goals

- Bundling CurseForge or Microsoft accounts.
- Redistributing a preassembled third-party modpack archive.
- Installing server-only mods into the client.
- Mod updates independent of the supplied manifest.
- Supporting unsupported Windows releases without a separate compatibility test.
