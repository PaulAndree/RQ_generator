# Codex workflow bootstrap tasks

All tasks remain pending until a human approves the requirements and design.

- [ ] T1. Capture missing-init and invalid-registry failures in temporary fixtures. Record the 32-test application baseline. Covers R1-R7.
- [ ] T2. Add the standard-library metadata validator and fixtures for valid state, invalid types, duplicate IDs and names, unknown status, multiple active features, missing or empty specs, escaping paths, missing or stale approval, missing review or PR, and blocked resume state. Covers R4-R7.
- [ ] T3. Add executable `init.sh` with explicit environment diagnostics, no installation, correct checkout selection, and failure propagation. Verify success and controlled failure paths including zero collected tests. Covers R1-R3.
- [ ] T4. Register native Codex roles, remove misleading hook JSON, and verify configuration loading with the recorded installed CLI version. Document runtime limits. Covers R9.
- [ ] T5. Add GitHub Actions using Python 3.12 and explicit dev setup before the same check command. Inspect permissions and record local versus hosted results separately. Covers R8.
- [ ] T6. Run `./init.sh`, preserve the existing 32 application tests, and write the R1-R9 evidence map with exact commands, outputs, and unavailable checks. Covers R1-R9.
- [ ] T7. Obtain independent review of the exact code commit, resolve findings, open the PR, and update canonical state with the real review and PR references. Leave merging to the human. Covers R7-R8.
