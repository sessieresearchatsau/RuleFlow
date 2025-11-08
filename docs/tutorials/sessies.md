# Repositories

> NOTE: An ongoing effort is in place to document all repositories either with pages on dedicated documentation sites or simply better READMEs. Please refer to the [Contribution Policy](policy/contribution-policy.md) for more details regarding repository documentation.

Here is the list of **all current repositories** containing the current state of the research: **<https://github.com/orgs/sessieresearchatsau/repositories>**. Each repository should have a short description, documentation, etc. Major repositories containing extensive content (or their own dedicated documentation site) are listed on this page.

## SSS-Papers

**Repository: <https://github.com/sessieresearchatsau/SSS-Papers>**

This repository is a workspace for research papers on Sequential Substitution Systems (SSS) and Indexed Concatenation (IC). It contains drafts, extended versions, diagrams, and presentation materials, keeping everything organized, versioned, and easy for collaborators to access. By gathering these materials in one place, the repository creates a clear record of our research and supports the preparation of future publications.

## SSS-Experiments

**Repository: <https://github.com/sessieresearchatsau/SSS-Experiments>**

This repository is a place for experimenting with ideas and implementations related to our research. It provides a shared space to try out approaches, test variations, and keep track of exploratory work. Each researcher gets a subdirectory named with their initials.


## Introductory Notebooks

**Documentation: <https://sessieresearchatsau.github.io/introductory-notebooks>**

The Introductory Notebooks repository provides a starting point for understanding Sequential Substitution Systems (SSS) and related concepts. It contains working notes (as PDFs and Mathematica Notebooks) that introduce core ideas such as rulesets, causal networks, enumeration methods, dimensionality, and indexed concatenation. These materials are designed to be both reference and sandbox: newcomers can use them to build intuition about the systems, while experienced contributors can adapt and extend them as the research develops.


## RuleFlow

**Documentation: <https://github.com/sessieresearchatsau/RuleFlow>**

RuleFlow is our custom (Python-based) engine for exploring how simple rule-based systems evolve and generate structure over time. At its core, it provides a flexible framework for defining rules, applying them to initial states, and recording the sequence of events that follow. Each event is tracked with explicit causal links—showing which cells were created, destroyed, or transformed—so that the resulting causal network can be studied in detail. By generalizing beyond narrow, one-off implementations, RuleFlow makes it possible to experiment with a wide range of substitution systems, compare different rulesets, and analyze emergent behaviors such as dimensionality, branching, etc. It is a complementary addition to the Mathematica Sessie code variants.
