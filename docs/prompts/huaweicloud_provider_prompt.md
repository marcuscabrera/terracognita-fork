# Prompt: Implement Huawei Cloud provider for TerraCognita

You are ChatGPT Codex acting as a senior Site Reliability Engineer contributing to TerraCognita. Extend the tool with a Terraform provider for Huawei Cloud while preserving the existing architecture.

## Context
- TerraCognita pulls existing infrastructure state from cloud APIs and emits Terraform HCL/state files using the shared `provider` interface defined in `provider/provider.go`.
- Providers live under their own top-level package (`aws/`, `google/`, `azurerm/`, `vsphere/`) and plug into the CLI through Cobra commands in `cmd/`.
- Writers (`writer/hcl`, `writer/state`) and filter mechanics (`filter/`) should not require structural changes; focus on wiring a new provider that adheres to current patterns.

## Objectives
1. Create a new `huaweicloud` package implementing `provider.Provider`.
2. Add a `cmd/huaweicloud` command mirroring the ergonomics of the other providers (flags, filters, logging, writer setup).
3. Support at least the core compute, networking, and storage resources exposed by the official Terraform Huawei Cloud provider (latest stable major).
4. Ensure generated HCL/state respects tagging filters and interpolation rules already enforced by the base importer.
5. Provide unit/integration coverage similar to existing providers.
6. Update documentation and changelog entries to teach users how to invoke the new provider.

## Implementation guidance
- Vendor the Terraform Huawei Cloud provider via `go.mod` and expose it from the new package’s `TFProvider()`.
- Introduce resource readers following the `reader`/`resources` split used elsewhere: a typed client that enumerates resources and maps them into Terraform schema data.
- Use caching helpers (see `cache/` and `util/`) to avoid redundant API calls when listing resources with dependencies.
- Leverage `filter.Filter` to honor `--include`, `--exclude`, `--targets`, and tag selectors, mirroring the AWS implementation for parity.
- Add any required normalization logic inside `FixResource` (e.g., sanitize defaulted attributes, ignore API-managed metadata).
- Wire the command into `cmd/root.go` so `terracognita huaweicloud ...` is available alongside existing commands. Support region selection and credential discovery via environment variables or CLI flags.
- Extend documentation (`README.md`, `docs/`) and release notes with usage examples, supported resource list, and prerequisites (IAM roles, environment vars).
- Update CI/test harnesses if additional environment variables or build tags are needed for Huawei Cloud.

## Deliverables
- New provider package with resource enumerators and Terraform client plumbing.
- CLI command and flag wiring for Huawei Cloud imports.
- Automated tests validating resource discovery and writer integration.
- Documentation updates (README, provider-specific docs) and changelog entries.
- Passing `go test ./...` and lint checks.

Focus on maintainability, parity with existing providers, and clear documentation so SREs can adopt Huawei Cloud with minimal friction.
