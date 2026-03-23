# slop-check

Anti-slop Python code reviewer. Evaluates files for failure modes that indicate code nobody fully owned.

## Usage
```
/slop-check [file_or_glob]
```

Defaults to git-staged Python files if no argument given.

Examples:
```
/slop-check src/retail/pipeline/transforms.py
/slop-check src/retail/**/*.py
/slop-check
```

## What it checks

**A. Slop verdict**: `clean` / `borderline` / `sloppy`

**B. Specific findings** (severity: high/medium/low):
- Fake certainty / placeholder assumptions ("adjust path if necessary", ungrounded imports)
- Over-abstraction without pressure (Manager/Processor/Helper wrappers, premature utilities)
- Exception handling that hides reality (bare `except Exception`, silent fallbacks, unbound retries)
- Verbosity that does not buy clarity (comments that restate code, enterprise naming for simple ops)
- Mismatch with Python norms (ignoring stdlib, Java/C# architecture pasted into Python)
- No evidence of local integration (doesn't match project patterns, adds deps without reason)
- PR-shaped code instead of problem-shaped code (mixes refactor+feature, solves imagined problem)

**C. Rewrite guidance**: fewest layers, direct stdlib, narrower exception scope, one coherent change

**D. Ownership test**: "Would the author explain every abstraction? Know which exceptions are intended? Still want this with AI unavailable?"

## What it does NOT penalise
- Short useful comments
- Clear type hints
- Small helpers with real reuse
- Concise AI-assisted code that is correct and well-integrated

## Implementation
Read the specified files and apply the evaluation criteria above. Output findings in this format:

```
=== SLOP CHECK: src/retail/pipeline/transforms.py ===
Verdict: clean

Findings: none

Ownership test: PASS — every function is direct, tested, and matches project patterns.
```
