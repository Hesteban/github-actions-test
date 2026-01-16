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

## 3. Conditionals: Running Steps/Jobs Only When Conditions Are Met

**Problem:** You want to skip or run specific steps/jobs based on conditions (OS, branch, event type, etc).

**Solution:** Use the `if:` keyword with conditional expressions.

### Common Conditional Contexts

| Context | Example | Use Case |
|---------|---------|----------|
| `runner.os` | `if: runner.os == 'Linux'` | Run only on specific OS |
| `github.ref` | `if: github.ref == 'refs/heads/main'` | Run only on specific branch |
| `github.event_name` | `if: github.event_name == 'push'` | Run only for specific events |
| `success()` | `if: success()` | Run if previous steps succeeded |
| `failure()` | `if: failure()` | Run if previous steps failed |
| `always()` | `if: always()` | Run regardless of previous status |

### Step-Level Conditionals

Run a step only on a specific OS:

```yaml
steps:
  - name: Mac Only Tool
    if: runner.os == 'macOS'
    run: echo "This only runs on Apple runners"

  - name: Ubuntu Only Tool
    if: runner.os == 'Linux'
    run: echo "This only runs on Ubuntu runners"

  - name: Windows Only
    if: runner.os == 'Windows'
    run: echo "This only runs on Windows runners"
```

### Job-Level Conditionals

Skip an entire job based on a condition:

```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/main'  # Only deploy from main branch
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying to production"
```

### Complex Conditionals

Combine multiple conditions with `&&` (AND) and `||` (OR):

```yaml
- name: Run tests on main branch
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  run: npm test

- name: Notify on failure
  if: failure() || github.event_name == 'workflow_dispatch'
  run: echo "Something went wrong or manual trigger"
```

### Job Status Functions

**Success/Failure Workflow:**

```yaml
steps:
  - name: Run Tests
    run: npm test

  - name: Cleanup on Success
    if: success()
    run: echo "Tests passed!"

  - name: Send Alert on Failure
    if: failure()
    run: echo "Tests failed! Sending alert..."

  - name: Generate Report
    if: always()  # Always runs, regardless of previous outcomes
    run: echo "Generating final report..."
```

### Conditional Environment Variables

Skip based on secrets or variables:

```yaml
- name: Deploy if credentials exist
  if: env.DEPLOY_KEY != ''
  env:
    DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
  run: ./deploy.sh
```

### Best Practices
- ✅ Use `if: always()` for cleanup or notification steps
- ✅ Use `if: failure()` for error handling
- ✅ Use `if: success()` for dependent steps
- ✅ Keep conditionals simple; use jobs for complex logic
- ✅ Test conditionals carefully in pull requests first

---

# 🏗️ GitHub Actions: Level 4 Summary

**Focus:** Modular Architecture, Reusable Actions, and Deployment Environments.

## 1. Composite Actions: Modular Reusable Architecture

**Problem:** You have repetitive workflow steps that you use across multiple workflows. Copying/pasting causes maintenance headaches.

**Solution:** Create a **Composite Action** - a reusable bundle of steps that can be used like a single action.

### What is a Composite Action?

A composite action is:
- A directory in `.github/actions/` with an `action.yml` file
- Contains one or more steps that run together
- Can accept inputs and produce outputs
- Called from workflows using `uses: ./.github/actions/action-name`

### Creating a Composite Action

**Folder structure:**
```
.github/
  actions/
    my-action/
      action.yml
      script.sh (optional)
```

**Example `action.yml`:**
```yaml
name: My Composite Action
description: A reusable action that does something useful

inputs:
  user_name:
    description: Name of the user
    required: true
    default: 'Guest'

outputs:
  random_id:
    description: Generated random ID
    value: ${{ steps.generator.outputs.id }}

runs:
  using: composite
  steps:
    - name: Generate ID
      id: generator
      shell: bash
      run: |
        RANDOM_ID=$(openssl rand -hex 4)
        echo "id=$RANDOM_ID" >> $GITHUB_OUTPUT
        echo "Generated ID for user: ${{ inputs.user_name }}"

    - name: Display Result
      shell: bash
      run: echo "Action completed for ${{ inputs.user_name }}"
```

### Using a Composite Action in a Workflow

```yaml
jobs:
  use-action:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run My Action
        id: my_action
        uses: ./.github/actions/my-action
        with:
          user_name: 'Alice'

      - name: Use Action Output
        run: echo "Generated ID: ${{ steps.my_action.outputs.random_id }}"
```

### Key Concepts

| Concept | Explanation |
|---------|-------------|
| **inputs** | Parameters passed to the action from workflow |
| **outputs** | Values the action returns to the workflow |
| **shell: bash** | Required for each step in composite action |
| **${{ inputs.name }}** | Access input values |
| **${{ steps.step_id.outputs.name }}** | Access step outputs within the action |
| **value:** | Maps action output to a step's output |

### Benefits of Composite Actions

- ✅ **DRY Principle:** Write once, use everywhere
- ✅ **Maintainability:** Update logic in one place
- ✅ **Consistency:** Same behavior across all workflows
- ✅ **Versioning:** Can tag versions in git
- ✅ **Team Collaboration:** Share reusable workflows

### Real-World Example: Deploy Action

```yaml
# .github/actions/deploy/action.yml
name: Deploy to Server
description: Deploys application to specified environment

inputs:
  environment:
    description: Deployment environment (dev, staging, prod)
    required: true
  version:
    description: Version to deploy
    required: true

runs:
  using: composite
  steps:
    - name: Validate Environment
      shell: bash
      run: |
        if [[ "${{ inputs.environment }}" != "dev" && \
              "${{ inputs.environment }}" != "staging" && \
              "${{ inputs.environment }}" != "prod" ]]; then
          echo "Invalid environment"
          exit 1
        fi

    - name: Deploy
      shell: bash
      run: |
        echo "Deploying v${{ inputs.version }} to ${{ inputs.environment }}"
        ./deploy.sh ${{ inputs.environment }} ${{ inputs.version }}

    - name: Verify Deployment
      shell: bash
      run: ./verify.sh ${{ inputs.environment }}
```

**Using the composite action:**
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/deploy
        with:
          environment: production
          version: 1.0.0
```

---

## 2. Environments: Deployment Protection and Approvals

**Problem:** You need to prevent accidental deployments to production and require manual approval.

**Solution:** Use **Environments** with **Required Reviewers** protection rules.

### What is an Environment?

An environment is a named deployment target (dev, staging, production) with:
- Its own secrets and variables
- Protection rules (required approvals, deployment branches)
- Audit trail of all deployments

### Setting Up an Environment

1. Go to your GitHub repo → **Settings** → **Environments**
2. Click **New environment**
3. Name it (e.g., `production`)
4. Configure protection rules:
   - **Required reviewers:** Approvers must approve before deployment
   - **Deployment branches:** Only specific branches can deploy
5. Add environment-specific secrets if needed
6. Save

### Using Environments in Workflows

```yaml
jobs:
  deploy:
    environment: production  # Job will use production environment
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        run: echo "Deploying to production after approval..."
```

### Workflow Execution with Environment Protection

1. **Workflow reaches the job** with `environment: production`
2. **Workflow PAUSES** and shows "Waiting for review" status
3. **Reviewer gets notification** to approve/reject
4. **Reviewer approves** in GitHub UI under "Deployments" section
5. **Workflow resumes** and executes remaining steps

### Multi-Stage Deployment Pipeline

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test

  staging-deploy:
    needs: test
    environment: staging  # Auto-deploy to staging
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh staging

  production-deploy:
    needs: staging-deploy
    environment: production  # Requires approval before deploying
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh production
```

**Execution flow:**
1. ✅ Run tests
2. ✅ Auto-deploy to staging
3. ⏸️ **PAUSE** - Waiting for production approval
4. 👤 Reviewer approves in GitHub
5. ✅ Deploy to production

### Environment Secrets

Store deployment-specific secrets per environment:

```yaml
jobs:
  deploy:
    environment: production
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        env:
          # Only available in production environment
          DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}
          API_KEY: ${{ secrets.PROD_API_KEY }}
        run: ./deploy.sh
```

**Setup:**
1. Go to **Settings** → **Environments** → select environment
2. Under "Environment secrets," add secrets specific to that environment
3. These secrets are **only accessible** to jobs using that environment

### Environment Variables

Store non-sensitive configuration per environment:

```yaml
jobs:
  deploy:
    environment: production
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        env:
          LOG_LEVEL: ${{ vars.LOG_LEVEL }}
          API_ENDPOINT: ${{ vars.API_ENDPOINT }}
        run: ./deploy.sh
```

### Protection Rules Best Practices

| Rule | Use Case |
|------|----------|
| **Required reviewers** | Critical environments (production, compliance) |
| **Deployment branches** | Only allow main/master to deploy to production |
| **Dismissable reviews** | Deprecated reviews when code changes |
| **Custom deployment branches** | Release branches can deploy, feature branches cannot |

### Real-World Scenario

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      build_id: ${{ steps.build.outputs.id }}
    steps:
      - uses: actions/checkout@v4
      - id: build
        run: |
          BUILD_ID=$(date +%s)
          echo "id=$BUILD_ID" >> $GITHUB_OUTPUT

  dev-deploy:
    needs: build
    environment: development
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying build ${{ needs.build.outputs.build_id }} to dev"

  staging-deploy:
    needs: [build, dev-deploy]
    environment: staging
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying build ${{ needs.build.outputs.build_id }} to staging"

  prod-deploy:
    needs: [build, staging-deploy]
    environment: production
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying build ${{ needs.build.outputs.build_id }} to production (after approval)"
```

### Best Practices

- ✅ **Always require approval** for production deployments
- ✅ **Use environment secrets** for sensitive credentials (never hardcode)
- ✅ **Chain environments** in jobs for staged rollouts
- ✅ **Document approval procedures** in job step names
- ✅ **Review environment secrets** regularly for security
- ✅ **Set required reviewers** to multiple people for critical deployments
- ✅ **Monitor deployment audit logs** in Settings → Environments