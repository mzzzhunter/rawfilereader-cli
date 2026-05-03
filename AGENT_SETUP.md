# Agent Setup Guide — rawfilereader-cli

This guide explains how to give an AI agent (Claude or OpenAI Codex) the ability
to read Thermo Fisher `.raw` mass spectrometry files through `rawfilereader-cli`.
Every command outputs JSON on stdout; the agent calls them like any shell tool and
parses the result.

---

## Table of Contents

1. [One-time system setup](#1-one-time-system-setup)
2. [Verify the installation](#2-verify-the-installation)
3. [Claude Code (Anthropic)](#3-claude-code-anthropic)
4. [OpenAI Codex CLI](#4-openai-codex-cli)
5. [Python API integration](#5-python-api-integration)
   - [Claude API (tool use)](#51-claude-api-tool-use)
   - [OpenAI API (function calling)](#52-openai-api-function-calling)
6. [Skill walkthrough — max-intensity m/z per filter](#6-skill-walkthrough--max-intensity-mz-per-filter)
7. [Command quick reference](#7-command-quick-reference)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. One-time system setup

### 1.1 Install .NET 8

The Thermo RawFileReader library is a .NET assembly; Python communicates with it
via `pythonnet`.

**Windows** — download the installer from Microsoft:
```
https://dotnet.microsoft.com/download/dotnet/8.0
```

**Linux / Google Colab:**
```bash
wget -q https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
bash dotnet-install.sh --channel 8.0 --runtime dotnet
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="$HOME/.dotnet:$HOME/.dotnet/tools:$PATH"
```

### 1.2 Download the Thermo RawFileReader assemblies

The DLL files are published in the official Thermo GitHub repository:

```
https://github.com/thermofisherlsms/RawFileReader/tree/main/Libs/NetCore/Net8/Assemblies
```

The fastest way to get only the assembly folder (without cloning the whole repo):

```bash
git clone --filter=blob:none --no-checkout --sparse \
    https://github.com/thermofisherlsms/RawFileReader.git thermo-libs
cd thermo-libs
git sparse-checkout set Libs/NetCore/Net8/Assemblies
git checkout
cd ..
```

This creates `thermo-libs/Libs/NetCore/Net8/Assemblies/` with the required `.dll`
files.

### 1.3 Set environment variables

```bash
# Required — path to the .dll folder
export RAWFILEREADER_LIBS="$(pwd)/thermo-libs/Libs/NetCore/Net8/Assemblies"

# Required on Linux (Windows finds .NET automatically)
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="$HOME/.dotnet:$HOME/.dotnet/tools:$PATH"
```

Add these lines to your shell profile (`.bashrc`, `.zshrc`, or equivalent) so
they persist across sessions.

### 1.4 Install rawfilereader-cli

```bash
pip install "git+https://github.com/mzzzhunter/rawfilereader-cli.git"
```

Or install in editable mode for development:

```bash
git clone https://github.com/mzzzhunter/rawfilereader-cli.git
cd rawfilereader-cli
pip install -e .
```

---

## 2. Verify the installation

Run these commands against a real `.raw` file to confirm everything works end-to-end.

```bash
# Should print a JSON object with first_scan and last_scan
rawfilereader file scan_range --file /path/to/your.raw

# Expected output (example):
# {"first_scan": 1, "last_scan": 3842}
```

```bash
# Pretty-print full file metadata
rawfilereader --indent 2 file info --file /path/to/your.raw
```

```bash
# List all unique scan filter strings
rawfilereader file filters --file /path/to/your.raw
```

If any command fails, check stderr for a structured error message:

```json
{"error": "Cannot locate the RawFileReader DLL directory.", "type": "assembly_load_error", "details": {}}
```

The `type` field tells you exactly what went wrong (see [Troubleshooting](#8-troubleshooting)).

---

## 3. Claude Code (Anthropic)

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) is Anthropic's
official CLI agent. It has a Bash tool it can use to run shell commands.  The
`CLAUDE.md` file in your project root is read automatically at session start and
tells Claude how to use the tools available in this project.

### 3.1 Create `CLAUDE.md`

Create (or append to) `CLAUDE.md` in the directory where you run Claude Code:

```markdown
## Mass spectrometry file access — rawfilereader-cli

You have access to `rawfilereader`, a CLI that reads Thermo Fisher `.raw` files
and returns JSON. Use it via the Bash tool.

### Environment (already set in this shell)
- RAWFILEREADER_LIBS  — path to Thermo .dll assemblies
- DOTNET_ROOT         — .NET 8 runtime root (Linux)

### General usage pattern
```bash
rawfilereader [--indent N] GROUP COMMAND --file PATH [OPTIONS]
```
All output is compact JSON on stdout. Errors go to stderr with exit code 1.

### Command groups
- `file`    — file metadata, scan range, instrument info, filters, chromatograms
- `scan`    — per-scan data: info, stats, spectrum, profile, trailer, dependents
- `search`  — find scans by filter string, retention time, or scan number
- `analyze` — aggregate operations: summary, average spectra, bulk scan info

### Orient first — always run these before anything else
```bash
rawfilereader file info       --file run.raw   # name, date, operator
rawfilereader file scan_range --file run.raw   # {first_scan, last_scan}
rawfilereader analyze summary --file run.raw   # scan counts by MS order
rawfilereader file filters    --file run.raw   # all unique filter strings
```

### Common commands
```bash
rawfilereader scan stats          --file run.raw --scan_number 1
rawfilereader scan spectrum       --file run.raw --scan_number 1 --max_points 20
rawfilereader scan trailer        --file run.raw --scan_number 1
rawfilereader search by_filter    --file run.raw --filter_string "Full ms"
rawfilereader search by_rt        --file run.raw --retention_time 4.5
rawfilereader search rt_for_scan  --file run.raw --scan_number 1
rawfilereader analyze average_scans --file run.raw --first_scan 1 --last_scan 50
rawfilereader analyze scan_info_range --file run.raw --ms_order 2 --stream
rawfilereader file chromatogram_peaks --file run.raw --min_height 1e5
```

### Tips
- Pass `--indent 2` for readable output when inspecting manually.
- `--max_points -1` returns metadata only (no arrays) — check `point_count`
  before fetching full spectrum data.
- `--stream` on iterate commands emits one JSON object per line (NDJSON) —
  use for large files to avoid buffering.
- All retention times are in **minutes**.
- **See SKILL.md** for six ready-to-run multi-step analysis recipes
  (file overview, chromatogram peaks, MS² survey, averaged spectrum, and more).
```

### 3.2 Start a Claude Code session

```bash
# From your project directory (where CLAUDE.md lives):
claude

# Or point at your RAW file directory:
claude --project /path/to/ms/data
```

### 3.3 Example prompts and what Claude does

**Prompt:**
> What scan range does `sample.raw` cover, and how many scans are there?

**What Claude does:**
```bash
rawfilereader file scan_range --file sample.raw
# → {"first_scan": 1, "last_scan": 3842}
```
Then computes `last_scan - first_scan + 1 = 3842` and reports back.

---

**Prompt:**
> Give me the base-peak chromatogram between 2 and 10 minutes.

**What Claude does:**
```bash
rawfilereader file chromatogram --file sample.raw \
    --trace_type BasePeak --start_rt 2.0 --end_rt 10.0
# → {"times": [...], "intensities": [...]}
```

---

**Prompt:**
> Find all MS1 scans and show me the centroid spectrum for the most intense one.

**What Claude does — step 1:**
```bash
rawfilereader search by_filter --file sample.raw --filter_string "Full ms"
# → {"filter_string": "Full ms", "scan_numbers": [1, 3, 5, ...], "count": 1921}
```
**Step 2** — get stats for each scan to find the most intense:
```bash
rawfilereader scan stats --file sample.raw --scan_number 1
# → {"scan_number": 1, "base_peak_intensity": 9.12e7, "base_peak_mass": 445.11, ...}
```
**Step 3** — fetch the spectrum:
```bash
rawfilereader scan spectrum --file sample.raw --scan_number 1 --max_points 50
# → {"masses": [...], "intensities": [...], "point_count": 50}
```

---

**Prompt:**
> Run the max-intensity m/z skill across all filters and show me a table.

Claude will follow the recipe in `SKILL.md` automatically, chaining `file filters`
→ `search by_filter` → `scan stats` for every filter, then format a table.

---

## 4. OpenAI Codex CLI

[OpenAI Codex CLI](https://github.com/openai/codex) is OpenAI's terminal agent
that uses GPT-4o (or newer models) and can run shell commands. Configure it with
an `AGENTS.md` file at your project root.

### 4.1 Install the Codex CLI

```bash
npm install -g @openai/codex
export OPENAI_API_KEY="sk-..."
```

### 4.2 Create `AGENTS.md`

```markdown
## Mass spectrometry file access — rawfilereader-cli

You have access to `rawfilereader`, a CLI that reads Thermo Fisher `.raw` mass
spectrometry files and returns structured JSON on stdout.

### Prerequisites already set in this environment
- `RAWFILEREADER_LIBS` — path to Thermo RawFileReader .NET assemblies
- `DOTNET_ROOT` — .NET 8 runtime root (Linux only)

### Command structure
```
rawfilereader [--indent N] GROUP COMMAND --file PATH [OPTIONS]
```

### Command groups and key commands

**file** — file-level metadata and chromatograms
```bash
rawfilereader file info           --file F  # metadata + run header
rawfilereader file scan_range     --file F  # {first_scan, last_scan}
rawfilereader file filters        --file F  # {filters: [...]}
rawfilereader file instrument     --file F  # instrument count + info
rawfilereader file chromatogram   --file F  --trace_type BasePeak|TIC
    [--start_rt MIN] [--end_rt MIN] [--filter_string STR]
rawfilereader file chromatogram_peaks --file F [--smooth_window 5] [--min_height 1e5]
```

**scan** — per-scan data
```bash
rawfilereader scan info      --file F --scan_number N
rawfilereader scan stats     --file F --scan_number N  # base peak, TIC, mass range
rawfilereader scan spectrum  --file F --scan_number N [--max_points N]
rawfilereader scan profile   --file F --scan_number N [--max_points N]
rawfilereader scan trailer   --file F --scan_number N
rawfilereader scan filter    --file F --scan_number N
rawfilereader scan dependents --file F --scan_number N [--depth 1]
```

**search** — find scans
```bash
rawfilereader search by_filter    --file F --filter_string STR [--start_scan N] [--end_scan N]
rawfilereader search by_rt        --file F --retention_time MIN
rawfilereader search rt_for_scan  --file F --scan_number N
rawfilereader search iterate_filter --file F --filter_string STR \
    [--start_time MIN] [--end_time MIN] [--stream]
```

**analyze** — aggregates
```bash
rawfilereader analyze summary          --file F
rawfilereader analyze average_scans    --file F --first_scan N --last_scan N [--filter_string STR]
rawfilereader analyze scan_info_range  --file F [--ms_order INT] [--stream]
```

### Output format
- **Success:** JSON object on stdout, exit code 0
- **Error:** JSON `{"error": "...", "type": "...", "details": {...}}` on stderr,
  exit code 1

### Flags
| Flag | Meaning |
|---|---|
| `--max_points 0` | Return all data points (default) |
| `--max_points -1` | Omit arrays, return metadata + point_count only |
| `--max_points N` | Truncate arrays to first N points |
| `--stream` | Emit one JSON object per line (NDJSON) |
| `--indent N` | Pretty-print JSON with N spaces |

All retention times are in **minutes**.

### Workflow tips
- **Orient first:** run `file info`, `file scan_range`, `analyze summary`, and
  `file filters` before anything else — this avoids out-of-range scan/RT errors.
- **Metadata before arrays:** use `--max_points -1` to check `point_count` before
  loading full spectrum data.
- **Stream large sets:** use `--stream` with `analyze scan_info_range` or
  `search iterate_filter` to avoid buffering thousands of objects.
- **Narrow before iterating:** pass `--start_scan`/`--end_scan` to
  `search by_filter` before looping over `scan stats`.
- **RT navigation:** always resolve RT→scan via `search by_rt`; never guess
  scan numbers from retention times arithmetically.
- **See SKILL.md** for six ready-to-use multi-step analysis recipes.
```

### 4.3 Start a Codex session

```bash
# Interactive mode — full shell + conversation
codex

# Single-turn mode
codex "How many scans are in sample.raw?"
```

### 4.4 Example prompts

**Prompt:**
> Summarize sample.raw: how many scans per MS order?

**Codex runs:**
```bash
rawfilereader analyze summary --file sample.raw
# → {"summary": {"1": 1921, "2": 1921}}
```

---

**Prompt:**
> Extract the TIC chromatogram and find peaks.

**Codex runs:**
```bash
rawfilereader file chromatogram_peaks --file sample.raw \
    --trace_type TIC --smooth_window 7
# → {"trace_type": "TIC", "smooth_window": 7,
#    "times": [...], "smoothed_intensities": [...],
#    "peaks": [{"index": 412, "retention_time": 4.12,
#               "intensity": 2.3e8, "smoothed_intensity": 2.1e8}, ...],
#    "peak_count": 34}
```

---

**Prompt:**
> For scan 42 show me the top 10 peaks and also the trailer data.

**Codex runs both in parallel:**
```bash
rawfilereader scan spectrum --file sample.raw --scan_number 42 --max_points 10
rawfilereader scan trailer  --file sample.raw --scan_number 42
```

---

## 5. Python API integration

If you are building an agent with the Anthropic or OpenAI Python SDK, define
`rawfilereader` commands as callable tools and let the model invoke them.

### 5.1 Claude API (tool use)

```python
import subprocess, json, anthropic

client = anthropic.Anthropic()

def rawfilereader(*args: str, file: str) -> dict:
    """Run a rawfilereader command and return parsed JSON."""
    cmd = ["rawfilereader"] + list(args) + ["--file", file]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(json.loads(r.stderr)["error"])
    return json.loads(r.stdout)


# Define the tools the model can call
tools = [
    {
        "name": "rawfilereader",
        "description": (
            "Run a rawfilereader-cli command against a Thermo Fisher .raw file "
            "and get back a JSON result. Pass the command as a list of strings "
            "exactly as you would on the command line, e.g. "
            '["file", "scan_range", "--file", "run.raw"].'
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Full argument list including GROUP, COMMAND, and all "
                        "options. Example: "
                        '["scan", "stats", "--file", "run.raw", "--scan_number", "1"]'
                    ),
                }
            },
            "required": ["args"],
        },
    }
]


def process_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "rawfilereader":
        args = tool_input["args"]
        cmd = ["rawfilereader"] + args
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            return r.stderr  # return the error JSON so the model can react
        return r.stdout
    raise ValueError(f"Unknown tool: {tool_name}")


def run_agent(user_message: str, raw_file: str) -> str:
    system = (
        f"You are a mass spectrometry data analyst. "
        f"The user's RAW file is at: {raw_file}\n"
        "Use the rawfilereader tool to answer questions about the file.\n"
        "Always start by calling file info, file scan_range, analyze summary, "
        "and file filters to orient yourself before querying individual scans."
    )
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            system=system,
            tools=tools,
            messages=messages,
        )

        # Collect any text to return at the end
        final_text = ""

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            return final_text

        if response.stop_reason == "tool_use":
            # Add the assistant's response to the message history
            messages.append({"role": "assistant", "content": response.content})

            # Process every tool call in this turn
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = process_tool_call(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})
            # Loop — the model will now continue with the tool results


# Example usage
answer = run_agent(
    "What are the unique filter strings in this file, and how many scans "
    "match each one?",
    raw_file="sample.raw",
)
print(answer)
```

---

### 5.2 OpenAI API (function calling)

```python
import subprocess, json
from openai import OpenAI

client = OpenAI()

# Define rawfilereader as an OpenAI function tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "rawfilereader",
            "description": (
                "Run a rawfilereader-cli command against a Thermo Fisher .raw "
                "file. Pass the full argument list as a JSON array of strings, "
                'e.g. ["file", "scan_range", "--file", "run.raw"].'
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Full rawfilereader argument list, e.g. "
                            '["scan", "stats", "--file", "run.raw", '
                            '"--scan_number", "1"]'
                        ),
                    }
                },
                "required": ["args"],
            },
        },
    }
]


def call_rawfilereader(args: list[str]) -> str:
    cmd = ["rawfilereader"] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else r.stderr


def run_agent(user_message: str, raw_file: str) -> str:
    system = (
        f"You are a mass spectrometry analyst. The RAW file is: {raw_file}. "
        "Use the rawfilereader function to explore it. "
        "Always call file info, file scan_range, analyze summary, and file filters "
        "first to orient yourself before querying individual scans."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_message},
    ]

    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            tools=tools,
            messages=messages,
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)["args"]
                result = call_rawfilereader(args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
        else:
            return msg.content


# Example usage
answer = run_agent(
    "Summarize the file: scan count, MS orders, and RT range.",
    raw_file="sample.raw",
)
print(answer)
```

---

## 6. Skill library (`SKILL.md`)

`SKILL.md` at the repo root contains six ready-to-use multi-step recipes.
Each is a standalone Python function built on the shared `_run` / `_stream`
helpers. Point agents at this file for complex analyses.

| # | Skill | Commands used | Good prompt |
|---|---|---|---|
| 1 | **File overview** | `file info`, `file scan_range`, `analyze summary`, `file filters` | *"Summarise this RAW file"* |
| 2 | **Max-intensity m/z per filter** | `file filters`, `search by_filter`, `scan stats` | *"Which m/z dominates each filter?"* |
| 3 | **Chromatogram peak table** | `file chromatogram_peaks`, `search by_rt` | *"Find all elution peaks above 1e6 intensity"* |
| 4 | **Spectrum at retention time** | `search by_rt`, `scan stats`, `scan spectrum` | *"Show me the spectrum at 4.5 min"* |
| 5 | **MS² precursor survey** | `analyze scan_info_range --stream`, `scan trailer` | *"List every MS2 precursor with charge state"* |
| 6 | **Averaged spectrum** | `search by_filter`, `analyze average_scans` | *"Average all MS1 scans for a clean spectrum"* |

### Example — Skill 2 step-by-step (max-intensity m/z)

```bash
# Step 1 — list filter strings
rawfilereader file filters --file sample.raw
# → {"filters": ["FTMS + p NSI Full ms [200.00-2000.00]", ...]}

# Step 2 — scan numbers for each filter
rawfilereader search by_filter --file sample.raw \
    --filter_string "FTMS + p NSI Full ms [200.00-2000.00]"
# → {"scan_numbers": [1, 3, 5, ...], "count": 1921}

# Step 3 — base-peak stats per scan
rawfilereader scan stats --file sample.raw --scan_number 1
# → {"base_peak_mass": 445.1185, "base_peak_intensity": 9.123e7, ...}
```

Final table (sorted by intensity):
```
         m/z       intensity  filter
   445.1185    9.123e+07  FTMS + p NSI Full ms [200.00-2000.00]
   612.3041    3.457e+06  FTMS + c NSI d Full ms2 445.12@hcd28.00 [100.00-1500.00]
```

### Skills compose

```python
# Orient → find peaks → fetch spectrum → average background
overview = file_overview("run.raw")
peaks    = chromatogram_peak_table("run.raw", min_height=1e6)
spec     = spectrum_at_rt("run.raw", peaks[0]["retention_time"])
avg      = averaged_spectrum("run.raw", overview["filters"][0])
```

---

## 7. Command quick reference

| Group | Command | Required options | Key optional options |
|---|---|---|---|
| `file` | `info` | `--file` | |
| `file` | `scan_range` | `--file` | |
| `file` | `filters` | `--file` | |
| `file` | `instrument` | `--file` | |
| `file` | `chromatogram` | `--file` | `--trace_type`, `--start_rt`, `--end_rt`, `--filter_string`, `--mass_range` |
| `file` | `chromatogram_peaks` | `--file` | same + `--smooth_window`, `--min_height` |
| `scan` | `info` | `--file`, `--scan_number` OR `--ms_order` | `--stream` |
| `scan` | `stats` | `--file`, `--scan_number` | |
| `scan` | `spectrum` | `--file`, `--scan_number` | `--prefer_profile`, `--max_points` |
| `scan` | `profile` | `--file`, `--scan_number` | `--max_points` |
| `scan` | `filter` | `--file`, `--scan_number` | |
| `scan` | `trailer` | `--file`, `--scan_number` | |
| `scan` | `dependents` | `--file`, `--scan_number` | `--depth` |
| `search` | `by_filter` | `--file`, `--filter_string` | `--start_scan`, `--end_scan` |
| `search` | `by_rt` | `--file`, `--retention_time` | |
| `search` | `rt_for_scan` | `--file`, `--scan_number` | |
| `search` | `iterate_filter` | `--file`, `--filter_string` | `--start_time`, `--end_time`, `--stream` |
| `analyze` | `summary` | `--file` | |
| `analyze` | `average_scans` | `--file`, `--first_scan`, `--last_scan` | `--filter_string` |
| `analyze` | `scan_info_range` | `--file` | `--ms_order`, `--stream` |

### Global flags (before the group name)

| Flag | Default | Effect |
|---|---|---|
| `--indent N` | compact | Pretty-print JSON with N-space indent |
| `--version` | | Print version and exit |

### Per-command flags

| Flag | Commands | Effect |
|---|---|---|
| `--max_points 0` | `spectrum`, `profile` | Return all data points |
| `--max_points -1` | `spectrum`, `profile` | Omit arrays; return `point_count` only |
| `--max_points N` | `spectrum`, `profile` | Truncate arrays to N points |
| `--stream` | `scan info`, `search iterate_filter`, `analyze scan_info_range` | NDJSON output |

---

## 8. Troubleshooting

All errors are returned as JSON on **stderr** with a `type` field:

| `type` | Cause | Fix |
|---|---|---|
| `assembly_load_error` | DLL directory not found or wrong path | Check `RAWFILEREADER_LIBS` points to the folder containing `ThermoFisher.CommonCore.*.dll` files |
| `raw_file_error` | File unreadable, corrupt, or RT out of range | Verify the file path; check that the RT you requested falls within the file's retention time range |
| `scan_not_found` | Scan number outside file range | Check `file scan_range` first to know valid bounds |
| `not_open_error` | File handle not open | Usually a code bug; retry the command |
| `in_acquisition_error` | File is locked (instrument still writing) | Wait for acquisition to finish |
| `instrument_error` | Invalid instrument index | Use `file instrument` to confirm available instruments |
| `unexpected_error` | Unhandled exception | Check `details.traceback` in the error JSON for the Python stack trace |

### Quick diagnostic sequence

```bash
# 1. Confirm .NET is available
dotnet --version        # should print 8.x.x

# 2. Confirm the DLL directory is set and contains .dll files
ls "$RAWFILEREADER_LIBS"/*.dll | head -5

# 3. Confirm the CLI is installed
rawfilereader --version

# 4. Smoke-test against your file
rawfilereader file scan_range --file /path/to/your.raw
```

### Large files

- Use `--max_points -1` to retrieve only metadata (no arrays) when you first
  explore a spectrum.
- Use `--stream` with `analyze scan_info_range` to iterate millions of scans
  without buffering the entire result in memory.
- Narrow searches first: `search by_filter` with `--start_scan`/`--end_scan`
  before calling `scan stats` on every result.
