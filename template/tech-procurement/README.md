# Claude Rig Planner

[![Claude Code](https://img.shields.io/badge/Claude%20Code-Project-orange?style=for-the-badge&logo=anthropic)](https://github.com/anthropics/claude-code)
[![Use this template](https://img.shields.io/badge/Use%20this%20template-238636?style=for-the-badge&logo=github)](https://github.com/danielrosehill/Claude-Rig-Planner/generate)
[![Claude Code Projects](https://img.shields.io/badge/More%20Claude%20Code-Projects-blue?style=for-the-badge&logo=github)](https://github.com/danielrosehill/Claude-Code-Repos-Index)
[![GitHub Index](https://img.shields.io/badge/GitHub-Master%20Index-lightgrey?style=for-the-badge&logo=github)](https://github.com/danielrosehill/Start-Here)

A structured workspace template for planning computer hardware upgrades with Claude Code. Whether you're upgrading a gaming PC, workstation, homelab server, or managing multiple machines, this template provides an organized environment for AI-assisted hardware planning.

## Features

- **Structured context gathering** - Systematic collection of user preferences, budget constraints, and requirements
- **Hardware profiling** - Document current specs for compatibility analysis
- **Multi-machine support** - Plan upgrades for multiple computers in one workspace
- **Formal estimates** - Generate VAT-compliant quotes for business use
- **Currency localization** - All outputs in your preferred currency
- **Privacy-aware** - Tools to redact sensitive data before sharing

## Quick Start

1. **Use this template** - Click the green "Use this template" button above
2. **Clone your new repo** - `git clone <your-repo-url>`
3. **Open with Claude Code** - `cd Claude-Rig-Planner && claude`
4. **Run setup** - Type `/setup` to begin the initial interview

## Repository Structure

```
Claude-Rig-Planner/
├── context/              # User preferences, budget, hardware specs
│   ├── user-context.md   # Your preferences and requirements
│   ├── budget.md         # Budget constraints
│   └── machines/         # Hardware profiles per machine
├── inputs/               # Files for the agent to process
│   └── (screenshots, quotes, system exports)
├── data/                 # Retrieved pricing and specification data
├── outputs/              # Agent's analysis and recommendations
│   ├── analysis/         # Compatibility and bottleneck analysis
│   ├── estimates/        # Formal cost estimates
│   ├── recommendations/  # Component recommendations
│   └── reports/          # Summary reports
├── prompts/              # Your custom prompts and instructions
├── agent-instructions/   # Detailed agent behavior guidelines
└── .claude/commands/     # Slash commands for common workflows
```

## Slash Commands

| Command | Description |
|---------|-------------|
| `/setup` | Initial interview to gather your preferences, budget, and requirements |
| `/profile` | Scan and document hardware specifications for a machine |
| `/analyze` | Run compatibility and bottleneck analysis |
| `/recommend` | Generate upgrade recommendations within your budget |
| `/estimate` | Create formal cost estimates (VAT-compliant if needed) |
| `/compare` | Compare specific components side-by-side |

## Workflow

### 1. Initial Setup
Run `/setup` to complete the initial interview. The agent will ask about:
- Your location and preferred currency
- Budget constraints (total and per-component)
- Preferred vendors and brands
- Use case (gaming, AI/ML, content creation, etc.)
- Business context (if estimates need VAT formatting)

### 2. Hardware Profiling
Run `/profile` to document your current hardware. The agent can:
- Scan local machines directly
- Connect via SSH to network machines
- Process screenshots or exports you place in `/inputs/`
- Accept manual specification input

### 3. Analysis & Recommendations
Run `/analyze` to identify bottlenecks and upgrade opportunities, then `/recommend` to get specific component suggestions within your budget.

### 4. Estimates
Run `/estimate` to generate formal quotes. Business users can get VAT-compliant estimates suitable for accountant review or internal approval.

## Providing Input

Place files in the `/inputs/` directory for the agent to process:
- **Screenshots** - Shopping cart images, spec screenshots
- **System exports** - JSON/CSV from hardware detection tools
- **Quotes** - Existing quotes or invoices for comparison

## Recommended MCP Servers

For enhanced functionality, consider installing these MCP servers:

| MCP | Purpose |
|-----|---------|
| **Context7** | Up-to-date hardware specifications |
| **TIME** | Accurate date/time for profiles and estimates |
| **Browser/WebFetch** | Retrieve current pricing from vendors |
| **Notion** | Export documents to Notion |
| **Resend** | Email estimates to yourself or accountant |

See [agent-instructions/mcp-recommendations.md](agent-instructions/mcp-recommendations.md) for setup details.

## Multi-Machine Planning

This template supports planning upgrades for multiple computers:
- Each machine gets its own profile in `/context/machines/{name}/`
- Track per-machine and aggregate budgets
- Cross-reference shared components for bulk purchasing
- Generate consolidated reports

## Privacy

Before sharing your workspace:
- The agent will offer to redact serial numbers and sensitive data
- `/inputs/` may contain personal screenshots - review before sharing
- `/context/business.md` contains business details - exclude if sharing publicly


## License

MIT License - see [LICENSE](LICENSE) for details.

---

To view an index of my Claude Code related projects, [click here](https://github.com/danielrosehill/Claude-Code-Repos-Index).
