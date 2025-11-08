# 🧩 Contribution Policy

This policy outlines how team members should upload, write, and push content to GitHub to maintain clarity, traceability, and version integrity across our evolving systems.

## General Principles

- Every contribution should be **intentional**, **documented**, and **reversible**.
- Use [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`) to communicate changes clearly.
- Follow a [branching strategy](https://nvie.com/posts/a-successful-git-branching-model/) that supports parallel development and clean releases.
- Use [GitHub Issues](https://docs.github.com/en/issues) to propose changes, raise questions, or document bugs before pushing major updates.
- Make sure to intentionally choose between "Private" or "Public" when creating new repositories. This ensures that we properly protect our intellectual property. In order to change a current repository, follow these steps: <kbd>[select repository] ➞ Settings ➞ General ➞ Change Visibility [at bottom of page]</kbd>. Please consult an administrator for determining such settings.

## Branching Model

We follow a simplified version of [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/) (Please **read the article** at this link):

| Branch Type     | Purpose                              | Naming Convention     |
|------------------|--------------------------------------|------------------------|
| `main`           | Stable, production-ready code        | —                      |
| `develop`        | Latest working version               | —                      |
| `feature/*`      | New features or experiments          | `feature/graph-viz`    |
| `release/*`      | Final prep before merging to `main`  | `release/v1.2.0`       |
| `hotfix/*`       | Emergency fixes to `main`            | `hotfix/typo-fix`      |

### Workflow Summary

1. **Open an Issue**  
   - Describe the proposed change, bug, or idea.
   - Use labels like `enhancement`, `bug`, or `discussion`.

2. **Start a Feature Branch**  
   `git checkout -b feature/my-feature develop`

3. **Commit regularly** with clear messages:  
   `git commit -m "Add causal graph rendering"`

4. **Push to remote**:  
   `git push origin feature/my-feature`

5. **Open a Pull Request (PR)** to `develop`  
   Include:
   - Summary of changes
   - Related issue or task
   - Any breaking changes or version bumps
   - Discussions and revision can be had at this stage (on GitHub)

6. **Merge with `--no-ff`** to preserve branch history.

> Rather than using the command line to operate Git, you may find the [GitHub Desktop Client](https://github.com/apps/desktop) to be much more user-friendly.

## Writing & Documentation

- Use Markdown for READMEs, glossaries, and guides. Because this website is also written in markdown, consider placing you documentation here, especially if the content is guides/glossaries. If the content is project-specific, either create another specialized [documentation site](https://docsify.js.org/), [GitHub Wiki](https://docs.github.com/en/communities/documenting-your-project-with-wikis) page, or simple [READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes). If the research being documented is primarily math-heavy/mathematica based, simply giving a short description in markdown and then linking to the PDF/Notebook is preferred. **Please remember** to properly link all documentation to the main documentation hub (this website), usually in the [Research Progress > Projects](progress/projects.md).
- Follow [these instructions](https://github.com/sessieresearchatsau/sessieresearchatsau.github.io) for editing documentation and setting up new documentation (with GitHub Pages and/or Docsify). Every repository should have clear documentation, whether in a dedicated site, or as simple readme markdowns. Of course, notebook-heavy repositories carry their own documentation in virtue of being notebooks.
- Place clear comments (and docstrings) in your code. This ensures that others understand your code more easily. It also can be helpful for you when coming back to the code a while later.
- Keep definitions modular and reusable.
- Document assumptions, edge cases, and naming decisions.
- Prefer semantic clarity over cleverness.

## Versioning

We use [Semantic Versioning](https://semver.org/):

- `MAJOR`: incompatible API changes
- `MINOR`: backward-compatible features
- `PATCH`: bug fixes or minor edits

Tag releases like:  
`git tag -a v1.2.0 -m "Release causal graph module"`

## Clean-Up

- Delete feature branches after merging.
- Keep `develop` tidy—no broken builds.
- Archive deprecated modules with clear notes.

> “Every commit tells a story. Let’s make ours readable, reversible, and resilient.”
