# Resilience Agent Architecture

## Project Overview

The Resilience Agent is an AI-powered code review system that analyzes Pull Requests for production resilience risks. It detects missing circuit breakers, timeout configurations, breaking API changes, and other failure modes that could cause production outages.

The system uses a **layered architecture** with three key components:
1. **Commands** - User-facing orchestration
2. **Subagents** - Specialized analysis agents
3. **Skills** - Auto-discovered reusable capabilities

---

## Architecture Layers

### Commands (User-Facing Orchestration)

**Location:** `.claude/commands/`

Commands are **slash commands** that users invoke to trigger workflows. They orchestrate the entire analysis pipeline from PR acquisition to final report generation.

**Example:** `/analyze-pr microservices-demo 2876`

**Responsibilities:**
- Parse user input (repo name, PR number)
- Navigate to repository and fetch PR
- Coordinate subagent execution
- Handle errors and edge cases
- Present results to user

**Current Commands:**
- `analyze-pr.md` - Main PR analysis orchestrator

**Key Characteristics:**
- User-invoked (not automatic)
- High-level workflow coordination
- Error handling and user feedback
- No deep analysis logic (delegates to subagents)

---

### Subagents (Specialized Analysts)

**Location:** `.claude/agents/`

Subagents are **specialized AI agents** that perform specific analysis tasks. They are launched by commands using the Task tool and operate independently with their own instructions.

**Why Subagents?**

1. **Separation of Concerns**
   - Each subagent focuses on one analysis type
   - risk-analyzer: Detects resilience issues
   - critic-agent: Validates findings quality

2. **Specialized Expertise**
   - risk-analyzer has deep knowledge of resilience patterns
   - critic-agent has expertise in false positive detection

3. **Independent Testing**
   - Each subagent can be tested in isolation
   - Examples validate specific detection patterns

4. **Composability**
   - Subagents can be reused in different workflows
   - Easy to add new agents (e.g., security-analyzer)

**What's in a Subagent?**

Each subagent has a definition file (`.md`) with:
- Name and description
- Mission statement
- Detection patterns to look for
- Output format specification
- Examples of what to detect

**Example: risk-analyzer.md**
```markdown
---
name: risk-analyzer
description: Detects change risks, failure modes, breaking changes
tools: Read, Grep, Glob, Bash
model: sonnet
---

# Your Mission
From the PR diff, identify:
1. New failure modes (APIs without circuit breakers)
2. Breaking API changes
3. Test recommendations
```

**Current Subagents:**
- `risk-analyzer.md` - Analyzes code changes for resilience risks
- `critic-agent.md` - Validates findings and filters false positives

**Key Characteristics:**
- Launched via Task tool by orchestrator
- Run independently with full context
- Have access to all project skills automatically
- Output structured data (JSON/Markdown)

---

### Skills (Reusable Capabilities)

**Location:** `.claude/skills/<skill-name>/SKILL.md`

Skills are **auto-discovered capabilities** that provide specialized knowledge Claude can use when relevant. They are NOT explicitly invoked—Claude automatically loads them based on task context.

**Why Skills?**

1. **Automatic Discovery**
   - No need to reference skills in subagent prompts
   - Claude scans and matches skills automatically
   - Reduces coupling between agents and capabilities

2. **Context Efficiency (Progressive Disclosure)**
   - Level 1: Name + description loaded at startup
   - Level 2: SKILL.md body loaded only when needed
   - Level 3: Additional resources on demand
   - Keeps context window small

3. **Reusability Across Agents**
   - git-risk-analysis skill can be used by any agent
   - No duplication of logic
   - Consistent methodology

4. **Composability**
   - Skills can build on each other
   - Easy to add new specialized knowledge

**What's in a Skill?**

**Frontmatter:**
```markdown
---
name: git-risk-analysis
description: Analyze git history to enhance risk assessment for PR reviews. Use when analyzing file changes to detect code hotspots, authorship patterns, rollback history.
allowed-tools: [Bash]
---
```

**Body:**
- Step-by-step instructions
- Command examples
- Interpretation guidelines
- Integration patterns

**How Auto-Discovery Works:**

From official Anthropic documentation:

1. **Startup:** Claude loads skill name + description into system prompt
2. **Task Execution:** Claude scans available skills for relevant matches
3. **Loading:** When match found, Claude reads SKILL.md body progressively
4. **Invocation:** Claude uses skill instructions autonomously

**IMPORTANT:** Subagents do NOT need to mention skills in their prompts. If a subagent is "analyzing file changes" and the git-risk-analysis skill description says "Use when analyzing file changes," Claude automatically discovers and uses it.

**Current Skills:**
- `git-risk-analysis/SKILL.md` - Git history analysis for risk scoring

**Key Characteristics:**
- Model-invoked (automatic)
- Description-driven discovery
- Progressive loading
- Tool restrictions via `allowed-tools`

---

## How Components Work Together

### Data Flow Example: /analyze-pr microservices-demo 2876

**Step 1: User Invokes Command**
```
User: /analyze-pr microservices-demo 2876
```

**Step 2: Command Orchestrates**
```
analyze-pr.md (orchestrator):
1. Navigate to microservices-demo/
2. Fetch PR #2876 from GitHub
3. Generate diff -> output/pr-2876/pr.diff
4. Create metadata.json
5. Launch risk-analyzer subagent
```

**Step 3: Subagent Analyzes (with Auto-Discovered Skills)**
```
risk-analyzer (subagent):
1. Read pr.diff
2. Detect language (Java, Go, Node.js)
3. Scan for resilience patterns
4. [AUTOMATIC] Claude sees "analyzing file changes"
5. [AUTOMATIC] Claude loads git-risk-analysis skill
6. [AUTOMATIC] Uses skill to check code churn, rollback history
7. Generate risk-analysis.json
```

Note: The subagent did NOT explicitly say "use git skill." Claude discovered it automatically because the task (analyzing files) matched the skill description.

**Step 4: Quality Gate**
```
critic-agent (subagent):
1. Read risk-analysis.json
2. Validate finding quality
3. Filter false positives
4. Generate final-report.md
```

**Step 5: Present Results**
```
analyze-pr.md (orchestrator):
1. Display final-report.md to user
2. Show artifact locations
```

### Skill Discovery in Action

**Subagent Prompt (risk-analyzer):**
```
Analyze PR #2876 for resilience issues.
Context: PR Diff at output/pr-2876/pr.diff
```

**What Happens Behind the Scenes:**
1. Claude starts analyzing the diff
2. Claude identifies task involves "file changes"
3. Claude scans skills: "git-risk-analysis - Use when analyzing file changes"
4. MATCH! Claude loads git-risk-analysis/SKILL.md
5. Claude follows skill instructions to run git commands
6. Claude enhances findings with git metrics

**No Explicit Reference Needed!** The skill description triggers automatic discovery.

---

## File Structure

```
reselience-agent-prototype/
├── .claude/
│   ├── commands/
│   │   └── analyze-pr.md           # Orchestrator (user-facing)
│   ├── agents/
│   │   ├── risk-analyzer.md        # Subagent: Risk detection
│   │   └── critic-agent.md         # Subagent: Quality validation
│   └── skills/
│       └── git-risk-analysis/
│           └── SKILL.md            # Skill: Git history analysis
├── examples/
│   └── change-risk/
│       └── java-resilience4j/      # Detection examples
│           ├── missing-circuit-breaker.md
│           ├── missing-timeout.md
│           └── retry-without-circuit.md
├── output/
│   └── pr-<NUMBER>/                # Analysis results
│       ├── metadata.json
│       ├── pr.diff
│       ├── risk-analysis.json
│       └── final-report.md
├── docs/
│   ├── ARCHITECTURE.md             # This file
│   └── GETTING-STARTED.md          # Tutorial
└── README.md
```

---

## Design Principles

### 1. Agent-First Architecture

Commands provide **goals**, not step-by-step scripts. Agents autonomously decide how to accomplish tasks using their tools and skills.

**Example:**
```markdown
Instead of:
  cd workspace/${REPO_NAME}
  git fetch origin pull/${PR_NUMBER}/head

We say:
  Navigate to repository {{repo_name}}
  Fetch PR #{{pr_number}} from GitHub
  Use your Bash tool and git skill to accomplish this.
```

### 2. Progressive Disclosure

Information is loaded only when needed:
- Commands: High-level orchestration
- Subagents: Detailed analysis logic
- Skills: Specialized knowledge (loaded on-demand)

### 3. Separation of Concerns

Each component has a single responsibility:
- Commands: Workflow coordination
- Subagents: Specialized analysis
- Skills: Reusable capabilities

### 4. Composability

Components are designed to work together:
- Skills can be used by any agent
- Agents can be invoked by any command
- Easy to add new capabilities

---

## Extending the System

### Adding a New Skill

1. Create `.claude/skills/<skill-name>/SKILL.md`
2. Write clear description with trigger keywords
3. Document step-by-step instructions
4. No need to update agent prompts (auto-discovery!)

### Adding a New Subagent

1. Create `.claude/agents/<agent-name>.md`
2. Define mission and detection patterns
3. Specify output format
4. Update command to invoke new agent

### Adding a New Command

1. Create `.claude/commands/<command-name>.md`
2. Define user input format
3. Orchestrate subagent invocations
4. Handle errors and present results

---

## Why This Architecture?

**Modularity**
- Each component can be developed independently
- Easy to test in isolation
- Clear boundaries and contracts

**Scalability**
- Add new skills without modifying agents
- Add new agents without changing commands
- Grow capabilities incrementally

**Maintainability**
- Single responsibility per component
- Changes localized to specific files
- Clear documentation for each layer

**AI-Native Design**
- Leverages Claude's autonomous decision-making
- Skills auto-discovery reduces coupling
- Progressive disclosure optimizes context usage

---

## References

- [Claude Code Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
- [Anthropic: Equipping Agents with Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Claude Code Subagents Documentation](https://docs.claude.com/en/docs/claude-code/sub-agents)
