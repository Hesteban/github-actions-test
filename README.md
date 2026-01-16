# 🚀 GitHub Actions: Level 1 Summary

**Focus:** Structure, Syntax, and Hierarchy.

## 1. The Component Hierarchy

A workflow follows a strict parent-child relationship:

- **Workflow:** The `.yml` file in `.github/workflows/`
- **Event (Trigger):** The condition that starts the workflow (e.g., `push`)
- **Job:** A unit of work that runs on a specific Runner (virtual machine). Jobs run in parallel by default.
- **Step:** Individual tasks within a job. They run sequentially.
- **Action/Run:** The actual command (`run`) or a reusable plugin (`uses`)

## 2. Essential Syntax Keyphrases

| Key | Purpose | Example |
|-----|---------|---------|
| `name` | Name of the workflow or step (shows in UI) | `name: CI Pipeline` |
| `on` | The event trigger | `on: [push, pull_request]` |
| `runs-on` | Defines the OS of the Runner | `runs-on: ubuntu-latest` |
| `uses` | Calls a pre-made Action (plugin) | `uses: actions/checkout@v4` |
| `run` | Executes shell commands | `run: npm install` |
| ` ``` ` | YAML symbol for multi-line scripts | — |

## 3. Common Events (`on:`)

- **push:** Runs when code is pushed to specific branches.
- **pull_request:** Runs when a PR is opened or updated (targets the merge preview).
- **workflow_dispatch:** Adds a manual "Run Workflow" button in the GitHub UI.
- **schedule:** Runs at specific times using POSIX cron syntax.

## 4. The "Golden Rule" of Level 1

### Don't forget the Checkout!

The Runner starts as a fresh, empty machine. To interact with your code, the first step in almost every job must be:

```yaml
- uses: actions/checkout@v4
```

---

# 🔐 GitHub Actions: Level 2 Summary

**Focus:** Contexts, Secrets, and Data Sharing.

## 1. Sharing Variables: The 3 Scopes

Understanding where a variable "lives" is the key to avoiding errors.

| Method | Scope | Syntax to Set | Syntax to Access | Use Case |
|--------|-------|---------------|------------------|----------|
| `env` (YAML) | Job/Step | `env: VAR: val` | `$VAR` | Hardcoded constants (URLs, Flags) |
| `$GITHUB_ENV` | Job (Internal) | `echo "K=V" >> $GITHUB_ENV` | `$K` | Dynamic values used in later steps |
| `$GITHUB_OUTPUT` | Cross-Job | `echo "K=V" >> $GITHUB_OUTPUT` | `${{ needs.J.outputs.K }}` | Passing data to different machines |

## 2. Managing Files (Artifacts)

Since every Job runs on a fresh machine, files do not persist automatically.

- **actions/upload-artifact@v4:** Saves a file/folder to GitHub's cloud storage.
- **actions/download-artifact@v4:** Retrieves that file in a subsequent Job.
- **Linkage:** Use the `needs: <job_id>` keyword to ensure the second job waits for the file to be ready.

## 3. Security (Secrets)

- **Storage:** Defined in Settings > Secrets and variables > Actions.
- **Masking:** GitHub automatically replaces secret values with `***` in the logs.
- **Best Practice:** Map secrets to Environment Variables within the step that needs them to limit exposure.

```yaml
steps:
  - name: API Call
    env:
      API_KEY: ${{ secrets.MY_SERVICE_KEY }}
    run: curl -H "Auth: $API_KEY" https://api.example.com
```

## 4. Summary Cheat Sheet: Passing Data

### A. Step A to Step B (Same Job)

Use the environment file to make a variable "sticky":

```yaml
- name: Generate
  run: echo "VERSION=1.0.${{ github.run_number }}" >> $GITHUB_ENV

- name: Reuse
  run: echo "The version is $VERSION"
```

### B. Job A to Job B (Different Jobs)

This requires a "bridge" in the YAML structure:

```yaml
jobs:
  job1:
    outputs:
      my_val: ${{ steps.provider.outputs.val }}
    steps:
      - id: provider
        run: echo "val=hello" >> $GITHUB_OUTPUT

  job2:
    needs: job1
    steps:
      - name: Use Output
        run: echo "Job 1 sent: ${{ needs.job1.outputs.my_val }}" # We access the output from the previous job via the 'needs' context
```

## 5. Built-in Contexts

GitHub provides objects full of metadata you can use anywhere:

- **`${{ github.actor }}`:** The user who triggered the workflow.
- **`${{ github.sha }}`:** The specific commit ID.
- **`${{ runner.os }}`:** The OS of the current machine (Linux, Windows, macOS).

## 6. Step Outputs vs Job Outputs

Understanding the difference is crucial for data flow across jobs:

### Step Output
- **Defined in:** A single step using `$GITHUB_OUTPUT`
- **Scope:** Available to **later steps in the same job**
- **Access syntax:** `${{ steps.<step_id>.outputs.<output_name> }}`

```yaml
- name: Generate Dynamic Name
  id: set_name
  run: echo "DYNAMIC_NAME=build-123.txt" >> $GITHUB_OUTPUT

- name: Use Output
  run: echo "File: ${{ steps.set_name.outputs.DYNAMIC_NAME }}"
```

### Job Output
- **Defined in:** The `outputs:` section of a job (references step outputs)
- **Scope:** Available to **other jobs that depend on this job** (via `needs:`)
- **Access syntax:** `${{ needs.<job_id>.outputs.<output_name> }}`

```yaml
build_job:
  outputs:
    filename: ${{ steps.set_name.outputs.DYNAMIC_NAME }}
  steps:
    - id: set_name
      run: echo "DYNAMIC_NAME=build-123.txt" >> $GITHUB_OUTPUT

deploy_job:
  needs: build_job
  steps:
    - run: echo "File: ${{ needs.build_job.outputs.filename }}"
```

### The Key Insight
Job outputs act as a **bridge** between jobs. They:
1. **Reference** a step output using `${{ steps.<step_id>.outputs.<name> }}`
2. **Get evaluated** after the job completes
3. **Become accessible** to other jobs via the `needs` context

**Chain:** `$GITHUB_OUTPUT` (step) → `steps.id.outputs.name` → `outputs: name:` (job) → `needs.job.outputs.name` (other jobs)

---

# ⚡ GitHub Actions: Level 3 Summary

**Focus:** Matrices, Caching, and Performance Optimization.

## 1. Matrix Strategy

Run the same job across multiple configurations automatically.

### Basic Matrix
Combines all values in each dimension:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    node-version: [18, 20, 22]
```

This creates **6 jobs** (2 OS × 3 Node versions).

### Matrix with Include
Add custom combinations that don't fit the standard matrix:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]
    node-version: [18, 20, 22]
  include:
    - os: ubuntu-latest
      node-version: 23
      experimental: true
```

This creates **7 jobs** (6 base + 1 custom).

### Accessing Matrix Variables
```yaml
runs-on: ${{ matrix.os }}
name: Test on ${{ matrix.os }} (Node ${{ matrix.node-version }})
```

### fail-fast: false
By default, if one matrix job fails, all others are cancelled. Set `fail-fast: false` to let all jobs complete.

## 2. Caching Dependencies

**Problem:** Installing dependencies (pip, npm, etc.) takes time. Repeated jobs re-download the same packages.

**Solution:** Cache them using `actions/cache@v3`.

### Python Example

```yaml
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip                              # Where pip stores packages
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}  # Unique cache ID
    restore-keys: |                                 # Fallback if exact key not found
      ${{ runner.os }}-pip-

- name: Install Dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
```

### How It Works

1. **`key`:** Unique identifier for the cache. When `requirements.txt` changes, the key changes → new cache created
2. **`path`:** Directory to cache (pip cache location)
3. **`restore-keys`:** Fallback patterns if exact key not found

### Node.js Example

```yaml
- name: Cache npm dependencies
  uses: actions/cache@v3
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-
```

### Benefits
- ✅ **Faster jobs:** Cached dependencies load in seconds
- ✅ **Reduced bandwidth:** Don't re-download unchanged packages
- ✅ **Cost savings:** Fewer API calls to package repositories

### Cache Invalidation
The cache automatically updates when:
- The `key` changes (e.g., `requirements.txt` is modified)
- The cache expires (default 7 days of inactivity)
- You manually delete it from Settings > Actions > Caches