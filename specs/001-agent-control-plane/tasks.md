# Tasks: Agentic Control Plane Runtime Separation

**Input**: Design documents from `/specs/001-agent-control-plane/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Fail-Fast Rule**: Every behavior task starts with a failing executable check or an exact contract assertion before implementation. No hidden fallback, guessed compatibility, or silent downgrade is allowed.

## Agent Ownership Lanes

Use these lanes when assigning work to parallel Codex agents. Each lane owns a disjoint write set unless a task explicitly says otherwise.

- **Runtime CLI Agent**: owns `pyproject.toml`, `src/gh_address_cr/cli.py`, `src/gh_address_cr/__main__.py`, and public command wiring.
- **Protocol Agent**: owns `src/gh_address_cr/agent/`, `src/gh_address_cr/core/models.py`, and protocol/manifest tests.
- **Lease Coordinator Agent**: owns `src/gh_address_cr/core/leases.py`, lease state transitions, conflict detection, and lease tests.
- **GitHub Evidence Agent**: owns `src/gh_address_cr/github/`, `src/gh_address_cr/evidence/`, side-effect idempotency, retry records, and GitHub IO tests.
- **Gate Agent**: owns `src/gh_address_cr/core/gate.py`, final-gate behavior, and gate tests.
- **Skill Adapter Agent**: owns `gh-address-cr/SKILL.md`, `gh-address-cr/scripts/cli.py`, `gh-address-cr/runtime-requirements.json`, `gh-address-cr/agents/`, `gh-address-cr/references/`, and skill boundary docs/tests.
- **Verification Agent**: owns test orchestration, task/spec coverage checks, and final validation commands in `tests/` and `specs/001-agent-control-plane/quickstart.md`.

## Parallel Execution Policy

- The Runtime CLI Agent and Skill Adapter Agent may work in parallel only after `T001-T010` establish the package and compatibility test skeletons.
- The Protocol Agent and Lease Coordinator Agent may work in parallel after `T011-T018` define failing schema and lease tests.
- The GitHub Evidence Agent and Gate Agent may work in parallel after the Protocol Agent lands `ActionResponse`, `EvidenceRecord`, and `SideEffectAttempt` models.
- GitHub side-effect publishing tasks must remain serialized by the GitHub Evidence Agent; parallel agents may prepare ledger evidence but must not post or resolve directly.
- The Verification Agent should run after each story phase and reject completion claims that lack exact test evidence.

## Format: `[ID] [P?] [Story] [Owner] Description`

- **[P]**: Can run in parallel with other tasks in the same phase if ownership lanes do not overlap.
- **[Story]**: User story label from `spec.md`; omitted for setup/foundation tasks.
- Every task names the file path it changes or verifies.

## Phase 1: Setup

**Purpose**: Create the physical runtime package surface without moving behavior yet.

- [ ] T001 [Runtime CLI Agent] Create runtime package directories under `src/gh_address_cr/` for `agent/`, `core/`, `github/`, `intake/`, and `evidence/`.
- [ ] T002 [Runtime CLI Agent] Add minimal package markers in `src/gh_address_cr/__init__.py`, `src/gh_address_cr/agent/__init__.py`, `src/gh_address_cr/core/__init__.py`, `src/gh_address_cr/github/__init__.py`, `src/gh_address_cr/intake/__init__.py`, and `src/gh_address_cr/evidence/__init__.py`.
- [ ] T003 [Runtime CLI Agent] Update `pyproject.toml` with runtime package metadata, Python `>=3.10`, setuptools package discovery from `src`, and console script `gh-address-cr = "gh_address_cr.cli:main"`.
- [ ] T004 [Runtime CLI Agent] Add module entrypoint `src/gh_address_cr/__main__.py` that invokes `gh_address_cr.cli.main`.
- [ ] T005 [Skill Adapter Agent] Add `gh-address-cr/runtime-requirements.json` declaring required runtime package name, minimum runtime version, supported protocol version range, and required public entrypoints.
- [ ] T006 [Verification Agent] Add shared test helpers for repo root, skill root, runtime source root, and command execution in `tests/helpers.py`.
- [ ] T007 [Verification Agent] Document the multi-agent ownership lanes in `specs/001-agent-control-plane/quickstart.md`.
- [ ] T008 [Verification Agent] Run `python3 -m unittest discover -s tests` and record the expected setup-only failures in `specs/001-agent-control-plane/quickstart.md`.

## Phase 2: Foundation

**Purpose**: Establish fail-fast contracts, schema validation, and minimal runtime wiring required by every story.

- [ ] T009 [P] [Verification Agent] Add a failing console entrypoint test for `gh-address-cr --help` and `python3 -m gh_address_cr --help` in `tests/test_runtime_packaging.py`.
- [ ] T010 [P] [Skill Adapter Agent] Add a failing shim delegation test that proves `python3 gh-address-cr/scripts/cli.py --help` exits non-zero with a clear runtime-missing error when the runtime is absent in `tests/test_skill_runtime_shim.py`.
- [ ] T011 [P] [Protocol Agent] Add failing ActionRequest schema tests for required fields, `item_id`, `role`, `allowed_actions`, and `required_evidence` in `tests/test_agent_protocol.py`.
- [ ] T012 [P] [Protocol Agent] Add failing ActionResponse schema tests for `fix`, `clarify`, `defer`, and `reject` outcomes with exact evidence assertions in `tests/test_agent_protocol.py`.
- [ ] T013 [P] [Lease Coordinator Agent] Add failing lease lifecycle tests for `active`, `released`, `expired`, and `rejected` transitions in `tests/test_claim_leases.py`.
- [ ] T014 [P] [Lease Coordinator Agent] Add failing conflict-key tests that reject overlapping write leases and allow read-only compatible leases in `tests/test_claim_leases.py`.
- [ ] T015 [P] [GitHub Evidence Agent] Add failing EvidenceRecord and SideEffectAttempt serialization tests in `tests/test_control_plane_workflow.py`.
- [ ] T016 [P] [Gate Agent] Add failing final-gate tests for unresolved threads, missing reply evidence, pending review, blocking local items, and missing validation evidence in `tests/test_control_plane_workflow.py`.
- [ ] T017 [Runtime CLI Agent] Implement fail-fast CLI argument parsing in `src/gh_address_cr/cli.py` with `--help`, command dispatch, and explicit unknown-command errors.
- [ ] T018 [Protocol Agent] Implement core dataclasses or typed models in `src/gh_address_cr/core/models.py` for `ReviewSession`, `WorkItem`, `ActionRequest`, `ActionResponse`, `EvidenceRecord`, `SideEffectAttempt`, `CapabilityManifest`, and `ClaimLease`.
- [ ] T019 [Protocol Agent] Implement protocol validation helpers in `src/gh_address_cr/agent/requests.py`, `src/gh_address_cr/agent/responses.py`, `src/gh_address_cr/agent/roles.py`, and `src/gh_address_cr/agent/manifests.py`.
- [ ] T020 [Lease Coordinator Agent] Implement lease lifecycle and conflict validation in `src/gh_address_cr/core/leases.py`.
- [ ] T021 [GitHub Evidence Agent] Implement append-only ledger primitives in `src/gh_address_cr/evidence/ledger.py`.
- [ ] T022 [Gate Agent] Implement gate result model and exact failure reasons in `src/gh_address_cr/core/gate.py`.
- [ ] T023 [Runtime CLI Agent] Add basic session persistence helpers in `src/gh_address_cr/core/session.py` without GitHub side effects.
- [ ] T024 [Verification Agent] Run `python3 -m unittest tests.test_runtime_packaging tests.test_agent_protocol tests.test_claim_leases tests.test_control_plane_workflow` and record failures that remain blocked by story work in `specs/001-agent-control-plane/quickstart.md`.

## Phase 3: User Story 6 - Runtime And Skill Separation (Priority: P1)

**Goal**: The runtime CLI is outside the packaged skill; the packaged skill contains only instructions, references, assets, assistant hints, and a thin compatibility shim.

**Independent Test**: Installing the runtime exposes `gh-address-cr` and `python3 -m gh_address_cr`; invoking the skill shim delegates to that runtime or fails loudly before mutating session state.

- [ ] T025 [P] [US6] [Runtime CLI Agent] Add failing packaging test that imports `gh_address_cr.cli` from `src/gh_address_cr/cli.py` and rejects importing runtime code from `gh-address-cr/` in `tests/test_runtime_packaging.py`.
- [ ] T026 [P] [US6] [Skill Adapter Agent] Add failing test that scans `gh-address-cr/` and rejects copied runtime modules outside approved shim/reference paths in `tests/test_skill_runtime_shim.py`.
- [ ] T027 [P] [US6] [Skill Adapter Agent] Add failing compatibility preflight tests for missing runtime, too-old runtime version, unsupported protocol version, and missing entrypoints in `tests/test_skill_runtime_shim.py`.
- [ ] T028 [US6] [Runtime CLI Agent] Implement package version and protocol version exports in `src/gh_address_cr/__init__.py`.
- [ ] T029 [US6] [Runtime CLI Agent] Implement runtime compatibility reporting in `src/gh_address_cr/cli.py` for `gh-address-cr adapter check-runtime`.
- [ ] T030 [US6] [Skill Adapter Agent] Replace `gh-address-cr/scripts/cli.py` with a compatibility shim that loads the installed runtime entrypoint or exits with a clear remediation message before session mutation.
- [ ] T031 [US6] [Skill Adapter Agent] Update `gh-address-cr/SKILL.md` to describe the packaged skill as a thin adapter and point all stateful work to the runtime CLI.
- [ ] T032 [US6] [Skill Adapter Agent] Update `gh-address-cr/references/` docs to remove any claim that the skill owns runtime state machines or GitHub side effects.
- [ ] T033 [US6] [Verification Agent] Update `README.md` to document separate runtime installation, packaged skill installation, and compatibility shim behavior.
- [ ] T034 [US6] [Verification Agent] Run `python3 gh-address-cr/scripts/cli.py --help` and assert the output either delegates to runtime help or fails loudly with no session mutation.
- [ ] T035 [US6] [Verification Agent] Run `python3 -m unittest tests.test_runtime_packaging tests.test_skill_runtime_shim` and update `specs/001-agent-control-plane/quickstart.md` with exact commands.
- [ ] T036 [US6] [Verification Agent] Verify `gh-address-cr/` contains no runtime package copy by running a path scan defined in `tests/test_skill_runtime_shim.py`.

## Phase 4: User Story 1 - Review Initialization And Inspection (Priority: P1)

**Goal**: A coordinator can inspect a PR, ingest normalized findings, initialize a session, and emit the first ActionRequest through the runtime CLI.

**Independent Test**: Given a fixture PR and normalized findings, `gh-address-cr review` creates a session, preserves finding provenance, and emits a valid ActionRequest without relying on skill-local runtime code.

- [ ] T037 [P] [US1] [Runtime CLI Agent] Add failing CLI tests for `gh-address-cr review <owner/repo> <pr>` session initialization in `tests/test_control_plane_workflow.py`.
- [ ] T038 [P] [US1] [Protocol Agent] Add failing ActionRequest emission tests for PR thread items, local finding items, role eligibility, and required evidence in `tests/test_agent_protocol.py`.
- [ ] T039 [P] [US1] [GitHub Evidence Agent] Add failing normalized findings ingestion tests for fixed `finding` blocks and narrative rejection in `tests/test_findings_intake.py`.
- [ ] T040 [US1] [Runtime CLI Agent] Implement `review` command routing in `src/gh_address_cr/cli.py`.
- [ ] T041 [US1] [Runtime CLI Agent] Implement session creation and status persistence in `src/gh_address_cr/core/session.py`.
- [ ] T042 [US1] [Protocol Agent] Implement ActionRequest generation for first available blocking item in `src/gh_address_cr/agent/requests.py`.
- [ ] T043 [US1] [GitHub Evidence Agent] Implement PR thread inspection adapter interfaces in `src/gh_address_cr/github/threads.py`.
- [ ] T044 [US1] [GitHub Evidence Agent] Implement normalized findings ingestion in `src/gh_address_cr/intake/findings.py`.
- [ ] T045 [US1] [GitHub Evidence Agent] Implement intake adapter dispatch in `src/gh_address_cr/intake/adapters.py`.
- [ ] T046 [US1] [Runtime CLI Agent] Add `threads` and `findings` command routing in `src/gh_address_cr/cli.py` for existing public surfaces.
- [ ] T047 [US1] [Verification Agent] Update `README.md` examples for runtime-owned `review`, `threads`, and `findings` commands.
- [ ] T048 [US1] [Verification Agent] Run `python3 -m unittest tests.test_control_plane_workflow tests.test_agent_protocol tests.test_findings_intake` and record exact failures or passes in `specs/001-agent-control-plane/quickstart.md`.

## Phase 5: User Story 2 - Agentic Resolution Loop (Priority: P1)

**Goal**: An AI agent consumes ActionRequest, returns ActionResponse, and the runtime validates outcome-specific evidence before any terminal state or side effect.

**Independent Test**: A malformed or evidence-light ActionResponse is rejected with exact validation errors; valid `fix`, `clarify`, `defer`, and `reject` responses update local state without hidden defaults.

- [ ] T049 [P] [US2] [Protocol Agent] Add failing tests for `fix` response evidence: files changed, validation commands, result summary, and lease ID in `tests/test_agent_protocol.py`.
- [ ] T050 [P] [US2] [Protocol Agent] Add failing tests for `clarify`, `defer`, and `reject` response evidence rules in `tests/test_agent_protocol.py`.
- [ ] T051 [P] [US2] [Runtime CLI Agent] Add failing CLI tests for `gh-address-cr agent next` and `gh-address-cr agent submit` in `tests/test_control_plane_workflow.py`.
- [ ] T052 [US2] [Protocol Agent] Implement outcome-specific ActionResponse validators in `src/gh_address_cr/agent/responses.py`.
- [ ] T053 [US2] [Runtime CLI Agent] Implement `agent next` command in `src/gh_address_cr/cli.py`.
- [ ] T054 [US2] [Runtime CLI Agent] Implement `agent submit` command in `src/gh_address_cr/cli.py`.
- [ ] T055 [US2] [Runtime CLI Agent] Update `src/gh_address_cr/core/workflow.py` to apply accepted local ActionResponse results to session state.
- [ ] T056 [US2] [Protocol Agent] Add machine-readable error codes for invalid ActionResponse submissions in `src/gh_address_cr/agent/responses.py`.
- [ ] T057 [US2] [Skill Adapter Agent] Update `gh-address-cr/SKILL.md` with the ActionRequest/ActionResponse contract and the allowed `fix`, `clarify`, `defer`, and `reject` outcomes.
- [ ] T058 [US2] [Skill Adapter Agent] Add assistant-specific protocol hints in `gh-address-cr/agents/openai.yaml`.
- [ ] T059 [US2] [Verification Agent] Update `specs/001-agent-control-plane/contracts/agent-protocol.md` if implementation exposes stricter validation error names.
- [ ] T060 [US2] [Verification Agent] Run `python3 -m unittest tests.test_agent_protocol tests.test_control_plane_workflow` and record exact evidence in `specs/001-agent-control-plane/quickstart.md`.

## Phase 6: User Story 5 - Multi-Agent Work Coordination (Priority: P1)

**Goal**: A coordinator can safely split work across specialized agents using capability manifests, claim leases, conflict keys, and serialized side effects.

**Independent Test**: Two independent items can be leased concurrently; conflicting file or side-effect ownership is rejected; stale or duplicate submissions do not mutate session state or GitHub.

- [ ] T061 [P] [US5] [Protocol Agent] Add failing CapabilityManifest tests for eligible roles, allowed actions, evidence formats, and protocol version compatibility in `tests/test_agent_protocol.py`.
- [ ] T062 [P] [US5] [Lease Coordinator Agent] Add failing tests for concurrent independent leases with distinct item IDs and non-overlapping conflict keys in `tests/test_claim_leases.py`.
- [ ] T063 [P] [US5] [Lease Coordinator Agent] Add failing tests for duplicate lease claims, stale lease submissions, expired leases, and cross-role submissions in `tests/test_claim_leases.py`.
- [ ] T064 [P] [US5] [Runtime CLI Agent] Add failing CLI tests for `gh-address-cr agent leases` and `gh-address-cr agent reclaim` in `tests/test_control_plane_workflow.py`.
- [ ] T065 [US5] [Protocol Agent] Implement CapabilityManifest loading and validation in `src/gh_address_cr/agent/manifests.py`.
- [ ] T066 [US5] [Lease Coordinator Agent] Implement claim, release, expire, reject, and reclaim operations in `src/gh_address_cr/core/leases.py`.
- [ ] T067 [US5] [Lease Coordinator Agent] Implement conflict-key calculation for item IDs, file ownership, thread ownership, and GitHub side-effect ownership in `src/gh_address_cr/core/leases.py`.
- [ ] T068 [US5] [Runtime CLI Agent] Implement `agent leases` and `agent reclaim` command routing in `src/gh_address_cr/cli.py`.
- [ ] T069 [US5] [Runtime CLI Agent] Update `src/gh_address_cr/core/workflow.py` so accepted submissions require an active compatible lease.
- [ ] T070 [US5] [GitHub Evidence Agent] Ensure lease events append evidence records through `src/gh_address_cr/evidence/ledger.py`.
- [ ] T071 [US5] [Skill Adapter Agent] Update `gh-address-cr/SKILL.md` with coordinator, fix-agent, review-agent, verifier-agent, docs-agent, and release-agent responsibilities.
- [ ] T072 [US5] [Verification Agent] Add multi-agent examples to `specs/001-agent-control-plane/quickstart.md` using separate `agent next` and `agent submit` commands for independent items.
- [ ] T073 [US5] [Verification Agent] Run `python3 -m unittest tests.test_claim_leases tests.test_agent_protocol tests.test_control_plane_workflow` and record exact evidence in `specs/001-agent-control-plane/quickstart.md`.

## Phase 7: User Story 4 - Final Gate Validation (Priority: P1)

**Goal**: The final gate is the only authority for completion and rejects unresolved remote work, missing replies, pending current-login reviews, blocking local items, and missing validation evidence.

**Independent Test**: A session cannot complete unless all remote and local completion conditions pass in one fresh final-gate run with exact machine-readable summary fields.

- [ ] T074 [P] [US4] [Gate Agent] Add failing tests for final-gate machine summary fields in `tests/test_final_gate.py`.
- [ ] T075 [P] [US4] [Gate Agent] Add failing tests for missing terminal reply evidence even when a thread is resolved in `tests/test_final_gate.py`.
- [ ] T076 [P] [US4] [Gate Agent] Add failing tests for current-login pending review detection in `tests/test_final_gate.py`.
- [ ] T077 [P] [US4] [Gate Agent] Add failing tests for missing validation evidence on terminal local findings in `tests/test_final_gate.py`.
- [ ] T078 [US4] [Gate Agent] Implement final-gate aggregation in `src/gh_address_cr/core/gate.py`.
- [ ] T079 [US4] [Gate Agent] Implement explicit final-gate failure codes in `src/gh_address_cr/core/gate.py`.
- [ ] T080 [US4] [Runtime CLI Agent] Wire `final-gate` command output and non-zero failure behavior in `src/gh_address_cr/cli.py`.
- [ ] T081 [US4] [GitHub Evidence Agent] Implement review-state provider interface in `src/gh_address_cr/github/reviews.py`.
- [ ] T082 [US4] [GitHub Evidence Agent] Implement thread-state provider fields required by final-gate in `src/gh_address_cr/github/threads.py`.
- [ ] T083 [US4] [Skill Adapter Agent] Update `gh-address-cr/SKILL.md` to forbid completion claims before `gh-address-cr final-gate` passes.
- [ ] T084 [US4] [Verification Agent] Update `README.md` final-gate section with required summary fields and failure semantics.
- [ ] T085 [US4] [Verification Agent] Run `python3 -m unittest tests.test_final_gate tests.test_control_plane_workflow` and record exact evidence in `specs/001-agent-control-plane/quickstart.md`.

## Phase 8: User Story 3 - Evidence Ledger And GitHub IO (Priority: P2)

**Goal**: The runtime records every decision, validation, GitHub side-effect attempt, reply URL, resolve state, retry, and resume token in an append-only ledger.

**Independent Test**: A simulated transient GitHub failure records retry evidence, avoids duplicate replies/resolves through idempotency keys, and returns a resume command without marking the item complete.

- [ ] T086 [P] [US3] [GitHub Evidence Agent] Add failing tests for append-only ledger ordering, actor role, lease ID, item ID, and timestamp fields in `tests/test_evidence_ledger.py`.
- [ ] T087 [P] [US3] [GitHub Evidence Agent] Add failing tests for reply-posted, reply-url, resolve-state, and idempotency-key evidence in `tests/test_evidence_ledger.py`.
- [ ] T088 [P] [US3] [GitHub Evidence Agent] Add failing tests for transient GitHub failure retry exhaustion and resume-token output in `tests/test_evidence_ledger.py`.
- [ ] T089 [US3] [GitHub Evidence Agent] Implement durable ledger append and load APIs in `src/gh_address_cr/evidence/ledger.py`.
- [ ] T090 [US3] [GitHub Evidence Agent] Implement audit helpers for evidence completeness in `src/gh_address_cr/evidence/audit.py`.
- [ ] T091 [US3] [GitHub Evidence Agent] Implement reply posting adapter with idempotency recording in `src/gh_address_cr/github/replies.py`.
- [ ] T092 [US3] [GitHub Evidence Agent] Implement thread resolve adapter with idempotency recording in `src/gh_address_cr/github/threads.py`.
- [ ] T093 [US3] [Runtime CLI Agent] Wire publish-ready workflow transitions in `src/gh_address_cr/core/workflow.py`.
- [ ] T094 [US3] [Runtime CLI Agent] Add resume-token display and recovery command output in `src/gh_address_cr/cli.py`.
- [ ] T095 [US3] [Skill Adapter Agent] Update `gh-address-cr/references/` to describe evidence-ledger audit expectations without exposing internal implementation APIs as agent-safe commands.
- [ ] T096 [US3] [Verification Agent] Run `python3 -m unittest tests.test_evidence_ledger tests.test_control_plane_workflow` and record exact evidence in `specs/001-agent-control-plane/quickstart.md`.

## Phase 9: Public Compatibility And Migration

**Purpose**: Preserve existing public command semantics while moving runtime ownership outside the skill.

- [ ] T097 [P] [Runtime CLI Agent] Add compatibility tests for existing public commands `review`, `threads`, `findings`, `adapter`, `review-to-findings`, `final-gate`, and `cr-loop --help` in `tests/test_runtime_packaging.py`.
- [ ] T098 [P] [Skill Adapter Agent] Add shim compatibility tests for legacy invocation `python3 gh-address-cr/scripts/cli.py <command>` in `tests/test_skill_runtime_shim.py`.
- [ ] T099 [Runtime CLI Agent] Preserve public command names and summary field names in `src/gh_address_cr/cli.py`.
- [ ] T100 [Skill Adapter Agent] Preserve skill-root-relative path language in `gh-address-cr/SKILL.md` and repo-root path language in `README.md`.
- [ ] T101 [Verification Agent] Update `specs/001-agent-control-plane/contracts/cli-contract.md` if compatibility behavior becomes stricter during implementation.
- [ ] T102 [Verification Agent] Run `python3 gh-address-cr/scripts/cli.py cr-loop --help` and record exact output expectation in `specs/001-agent-control-plane/quickstart.md`.

## Phase 10: Polish And Cross-Cutting Verification

**Purpose**: Prove the plan is complete, coherent, and executable before claiming the architecture migration is ready.

- [ ] T103 [P] [Verification Agent] Run `ruff check gh-address-cr src tests` and fix reported issues in the owning files.
- [ ] T104 [P] [Verification Agent] Run `python3 -m unittest discover -s tests` and record exact pass/fail evidence in `specs/001-agent-control-plane/quickstart.md`.
- [ ] T105 [P] [Verification Agent] Run `python3 gh-address-cr/scripts/cli.py --help` and record exact pass/fail evidence in `specs/001-agent-control-plane/quickstart.md`.
- [ ] T106 [P] [Verification Agent] Run `python3 -m gh_address_cr --help` and record exact pass/fail evidence in `specs/001-agent-control-plane/quickstart.md`.
- [ ] T107 [P] [Verification Agent] Run `python3 gh-address-cr/scripts/cli.py final-gate --help` and record exact pass/fail evidence in `specs/001-agent-control-plane/quickstart.md`.
- [ ] T108 [Verification Agent] Check every FR in `specs/001-agent-control-plane/spec.md` has at least one task in `specs/001-agent-control-plane/tasks.md`.
- [ ] T109 [Verification Agent] Check every public command in `specs/001-agent-control-plane/contracts/cli-contract.md` has a packaging or workflow test in `tests/`.
- [ ] T110 [Verification Agent] Check every ActionRequest, ActionResponse, ClaimLease, CapabilityManifest, EvidenceRecord, and SideEffectAttempt field in `specs/001-agent-control-plane/data-model.md` has validation coverage in `tests/`.
- [ ] T111 [Verification Agent] Run `git diff --check` for whitespace validation across `specs/001-agent-control-plane/tasks.md`, `README.md`, `gh-address-cr/SKILL.md`, and `src/gh_address_cr/`.
- [ ] T112 [Verification Agent] Produce a final implementation readiness note in `specs/001-agent-control-plane/quickstart.md` listing remaining blockers, verification commands, and which agent lane owns each blocker.

## Dependency Graph

- **Setup** (`T001-T008`) must complete before Foundation.
- **Foundation** (`T009-T024`) blocks all user stories.
- **US6** (`T025-T036`) should land before public runtime behavior is migrated, because it establishes the physical runtime/skill split.
- **US1** (`T037-T048`) depends on Foundation and US6.
- **US2** (`T049-T060`) depends on US1 ActionRequest generation.
- **US5** (`T061-T073`) depends on Foundation protocol models and can proceed after US2 validators exist.
- **US4** (`T074-T085`) depends on US1 session state and US2 terminal evidence semantics.
- **US3** (`T086-T096`) depends on US2 response semantics and feeds stronger evidence into US4.
- **Compatibility** (`T097-T102`) depends on US6 and the migrated public commands.
- **Polish** (`T103-T112`) depends on all story phases.

## Parallel Examples

### After Setup

- Runtime CLI Agent: `T009`, `T017`, `T023`
- Skill Adapter Agent: `T010`, `T026`, `T027`
- Protocol Agent: `T011`, `T012`, `T018`, `T019`
- Lease Coordinator Agent: `T013`, `T014`, `T020`
- GitHub Evidence Agent: `T015`, `T021`
- Gate Agent: `T016`, `T022`

### After US6

- Runtime CLI Agent can implement `T037`, `T040`, `T041`, `T046`.
- Protocol Agent can implement `T038`, `T042`, `T049`, `T050`, `T052`.
- GitHub Evidence Agent can implement `T039`, `T043`, `T044`, `T045`.
- Skill Adapter Agent can update `T057`, `T058`, `T071` without touching runtime code.

### Multi-Agent Coordination Slice

- Lease Coordinator Agent owns `T062`, `T063`, `T066`, `T067`.
- Runtime CLI Agent owns `T064`, `T068`, `T069`.
- GitHub Evidence Agent owns `T070`.
- Verification Agent owns `T072`, `T073`.

## MVP Scope Recommendation

The smallest useful MVP is **US6 + US1 + US2 + US5 + US4**:

1. Runtime and packaged skill are physically separate.
2. `review` initializes a session and emits ActionRequest.
3. agents submit validated ActionResponse evidence.
4. claim leases allow safe parallel work.
5. final-gate proves completion.

US3 should follow immediately after MVP because durable side-effect evidence and retry/resume behavior are required before using the system on high-risk PRs.

## Fail-Fast Checklist

- Every validator rejects malformed input with an exact error code.
- Every CLI command exits non-zero when required runtime, protocol, session, lease, or evidence data is missing.
- No task introduces a silent fallback from the packaged skill to copied runtime logic.
- No GitHub reply or resolve can occur before ActionResponse evidence validates.
- No completion claim is allowed before final-gate passes.
- No stale, duplicate, or cross-role lease submission mutates session state.
- No transient GitHub failure is hidden; retries, exhaustion, and resume commands are recorded in the ledger.
