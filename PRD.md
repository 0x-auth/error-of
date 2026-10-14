# PRD: error-of

**Status:** Draft v0.1

---

# Vision

Most software treats errors as failures.

`error-of` treats errors as observations.

The objective is not merely to recover from errors, but to discover the assumptions that produced them and suggest better representations.

---

# Problem

Today's tools answer questions like:

- What failed?
- Where did it fail?
- What was the stack trace?

They rarely answer:

- Why was this assumption invalid?
- What boundary did the system encounter?
- Can this limitation suggest a different representation?
- Has this pattern appeared before?

The result is that developers repeatedly solve similar classes of problems from scratch.

---

# Goal

Create a CLI that transforms execution failures into structured knowledge.

Input

- Command
- stdout
- stderr
- exit code
- runtime
- environment

Output

Boundary

↓

Observation

↓

Assumption

↓

Possible invariant

↓

Suggested transformations

↓

Knowledge

---

# Core Principle

Every limitation reveals an assumption.

Every assumption suggests a better representation.

---

# Design Principles

- Language agnostic
- Extensible
- Explain every inference
- Preserve original errors
- Deterministic where possible
- Learn without rewriting history

---

# User Stories

## Developer

Execute a command and receive both the original error and an explanation.

## Researcher

Discover recurring failure patterns across projects.

## Architect

Use limitations to improve system design.

---

# Non Goals

- Debugger
- Compiler
- Linter
- Automatic code fixer
- AI pair programmer

---

# MVP

Command

    error-of run <command>

Capture

- stdout
- stderr
- exit code
- runtime

Classify

- Memory
- Storage
- Time
- Precision
- Representation
- Authentication
- Permissions
- Network
- Syntax
- Context
- Unknown

Generate

- Markdown report
- JSON report

---

# Future Commands

error-of run

error-of explain

error-of classify

error-of infer

error-of transform

error-of report

error-of learn

error-of search

---

# Pipeline

Error

↓

Boundary

↓

Observation

↓

Assumption

↓

Invariant

↓

Representation

↓

Transformation

↓

Continuation

---

# Architecture

CLI

↓

Capture

↓

Normalize

↓

Classify

↓

Infer

↓

Transform

↓

Report

↓

Knowledge Base

---

# Knowledge Model

Case

↓

Boundary

↓

Transformation

↓

Outcome

↓

References

↓

Pattern

↓

Invariant

---

# Plugin Architecture

capture/

classifiers/

transformers/

reporters/

storage/

Each module should be replaceable.

---

# Success Metric

The goal is not to eliminate errors.

The goal is to learn from them.

A successful execution is one that discovers a better representation.

---

# Philosophy

Traditional software asks:

"How do we remove this error?"

error-of asks:

"What assumption did this error reveal?"

The answer often contains the next algorithm.
