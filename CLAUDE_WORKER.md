# Run Claude Code alongside Codex

The Claude worker proposes and checks gameplay changes. It pushes proposals under `claude/` in this repository. The scheduled Codex run checks those branches for candidates, and the existing three reviewers decide whether the exact gameplay commit enters the practice queue. The signed-in Chrome helper submits from that queue under the contest’s team limits.

## One-time setup

1. The repository owner invites the teammate under **Settings → Collaborators → Add people**. The teammate accepts the invite with their own GitHub account. [Repository access settings](https://github.com/atharvatripathi2026/gtgoats_mech_royale/settings/access)
2. On the computer that will run the worker, install Python 3.11 or newer, Git, Docker and an up-to-date Claude Code. Sign in to Claude Code with the teammate's Claude Max account. Configure Git to push to GitHub as the teammate. [Claude Code setup](https://code.claude.com/docs/en/setup) · [Use Claude Code with Max](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-max-or-ultra-plan)
3. Download and extract the official starter kit. The directory you pass to the worker should contain `arena/` and `check/check.py`. [Starter kit](https://www.joinbuilders.org/buildathon/tracks/builders/files/mechfight-kit.tar.gz)
4. Clone this repository, or update an existing checkout with `git pull --ff-only`. From the repo root, start the worker with the path to the extracted kit.

```sh
git clone https://github.com/atharvatripathi2026/gtgoats_mech_royale.git
cd gtgoats_mech_royale
python3 -m training.claude_worker --kit /absolute/path/to/mechfight-kit
```

Run the worker in Linux. On Windows, use a WSL2 Linux distribution with Docker Desktop integration and sign in to Claude Code inside WSL2. Keep the terminal or a process supervisor running, the computer awake, and Docker available. The worker polls every 15 minutes by default and stops at 11 a.m. Eastern on November 22, 2026. Ctrl+C stops the local process. Keep the existing Chrome helper running on the signed-in Builders tab.

To try one iteration locally before enabling the loop, add `--once --no-push` to the command. Watch for a JSON status line at the end of the iteration.

The worker calls the installed non-interactive Claude Code CLI with local login. Anthropic says this usage draws from the signed-in plan's limits. Authentication and usage limits can pause production until the session or allowance is available again. For a subscription-only run, disable Claude extra usage on the account. [Claude’s headless usage and billing guidance](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan)

## How candidates move through the workflow

- Claude receives the latest cycle handoff and proposes edits to gameplay files from the latest reviewed baseline. The teammate's machine runs the unit tests, official replay, and short paired simulations against the exact gameplay commit in Docker. A passing proposal branch ends in a separate report commit with a summary and check results.
- Codex discovers the branch from GitHub, verifies the gameplay SHA and parent, and runs its own review. Three actual approvals are required to publish to `practice-queue`. The report commit is a pointer for review. The entry uses the gameplay SHA.
- Chrome reads the same queue, verifies the team and available slots, and waits for the current practice run. Submissions and scorer receipts stay in the signed-in browser. The two producers share the existing four-attempt rolling limit.
