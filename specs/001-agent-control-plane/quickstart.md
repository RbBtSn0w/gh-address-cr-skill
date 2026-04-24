# Quickstart: Agent Control Plane

This quickstart describes the intended validation flow for the multi-agent
control-plane design. Some protocol commands are planned advanced/internal
commands and will become executable during implementation.

## 1. Run Existing Baseline Checks

```bash
python3 -m unittest discover -s tests
python3 gh-address-cr/scripts/cli.py --help
python3 gh-address-cr/scripts/cli.py cr-loop --help
```

## 2. Validate Runtime Installation

The target runtime entrypoint is:

```bash
python3 -m pip install -e .
gh-address-cr --help
python3 -m gh_address_cr --help
```

During migration, the skill-local shim remains available:

```bash
python3 gh-address-cr/scripts/cli.py --help
```

The shim must delegate to the installed runtime or fail loudly with remediation.

## 3. Start A Normal PR Session

The public entrypoint remains:

```bash
gh-address-cr review owner/repo 123
```

If the workflow returns `WAITING_FOR_EXTERNAL_REVIEW`, fill the handoff file
with findings JSON or fixed `finding` blocks, then rerun the same command.

## 4. Issue A Multi-Agent Action Request

Planned advanced/internal command:

```bash
gh-address-cr agent next owner/repo 123 --role fixer
```

Expected behavior:

- the CLI selects one eligible item
- the CLI creates one active `ClaimLease`
- the CLI writes an `ActionRequest`
- the AI fixer receives only the item, allowed actions, required evidence, and
  forbidden actions

## 5. Submit Agent Evidence

Planned advanced/internal command:

```bash
gh-address-cr agent submit owner/repo 123 --input action-response.json
```

Expected behavior:

- malformed JSON fails loudly
- stale or mismatched leases fail loudly
- missing evidence fails loudly
- accepted evidence is appended to the ledger
- GitHub side effects are still performed by the deterministic control plane

## 6. Verify Parallel Coordination

Create at least three independent items and issue separate fixer leases.

Expected behavior:

- one active lease per item
- no duplicate accepted submissions for the same active lease
- stale leases can be reclaimed
- verifier rejection returns the item to blocked/open state without GitHub
  side effects

## 7. Publish And Gate

After evidence is accepted, rerun:

```bash
gh-address-cr review owner/repo 123
gh-address-cr final-gate owner/repo 123
```

Completion can be claimed only after `final-gate` proves:

- zero unresolved GitHub threads
- zero current-login pending reviews
- zero session blocking items
- no terminal GitHub thread missing durable reply evidence
- required validation evidence is present for terminal findings and accepted
  fixes

## 8. Validate Runtime / Skill Separation

Expected requirements before implementation proceeds:

- direct runtime invocation and skill shim invocation report compatible status
  contracts
- missing runtime fails before session mutation
- incompatible runtime fails before session mutation
- skill-owned docs describe the runtime as an external prerequisite
- no skill Markdown is the only owner of a state transition, GitHub side
  effect, or final-gate rule
