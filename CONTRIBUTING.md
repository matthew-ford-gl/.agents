# Contributing

Thanks for your interest in contributing to the AI Agent & Skill Library.

## Quick workflow

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally.
3. **Create a branch** for your change:
   ```bash
   git checkout -b feature/your-change-name
   ```
4. **Make your changes** and commit them with a clear message:
   ```bash
   git commit -m "feat: add a short description of your change"
   ```
5. **Push** the branch to your fork:
   ```bash
   git push origin feature/your-change-name
   ```
6. **Open a Pull Request** to `master` on the original repository.

## What to contribute

- New agent definitions in `agents/<name>/AGENT.md`.
- New skills in `skills/<name>/SKILL.md`.
- Improvements to existing agents, skills, install/uninstall scripts, or documentation.

## Guidelines

- Follow the existing directory and naming conventions.
- Keep agent and skill definitions focused on a single responsibility.
- Test the install/uninstall scripts for your platform (`.ps1` for Windows, `.sh` for Mac) locally if you change them.
- Explain the "why" as well as the "what" in your PR description.

## Commit style

Use clear, descriptive commit messages in the imperative mood, for example:

- `feat: add dependency-reviewer agent`
- `fix: correct symlink path for Devin skills`
- `docs: update README with new skill`

## Code of conduct

Be respectful and constructive in all interactions.
