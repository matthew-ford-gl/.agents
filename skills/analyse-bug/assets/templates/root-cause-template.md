# ROOT-CAUSE — {bug description}

**Classification**: CODE | CONFIG | DEPLOYMENT | DATA | ENVIRONMENT
**Confidence**: {percentage} ({evidence level})
**Components affected**: {list}

## Symptom
{What the user experienced — one paragraph, plain language}

## Evidence Chain
{Ordered list — each item labelled with its source and value}
1. [CODE] {file}:{line} — {what it shows}
2. [DB] Query result: {field} = {value} — {what it means}
3. [LOG] {log field}: {value} — {what it proves}

## Root Cause
{The mechanism in one paragraph. Causal chain, plain language, no code snippets.}

## Fix
{What needs to change and where. Distinguish code change vs config change vs data fix.}

## Verification
{Specific query or check to confirm the fix is working after deployment}

## Regression Test
{What automated test should be added to prevent recurrence}
