# Coherence-CE Object Chunking and Manifest Semantics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add architecture artifacts that adapt IRTF CCNx chunking and FLIC manifest concepts into Coherence-CE object chunking, S3 multipart mapping, Git LFS gateway semantics, and RAG corpus ingestion boundaries.

**Architecture:** Coherence-CE keeps external API compatibility for S3, Git LFS, REST, and RAG tooling while internally representing large byte objects as immutable content-addressed chunks under an atomic manifest root. CCNx chunk numbering and FLIC-style manifest graphs are used as design references, not external wire-protocol requirements.

**Tech Stack:** Markdown ADR/report artifacts, OpenAPI 3.1 YAML, PlantUML generated through `scripts/generate_adr_diagrams.py`, Git LFS policy validation, Gitolite/GitHub-compatible Git workflow.

---

### Task 1: Capture source basis

**Files:**
- Create: `review-artifacts/ietf-icnrg-chunking-source-map.md`
- Create: `review-artifacts/ietf-icnrg-chunking-source-map.json`

- [x] **Step 1: Record source metadata**

Create a source-map entry for:
- `draft-irtf-icnrg-ccnxchunking-04`
- `draft-irtf-icnrg-flic-07`
- RFC 8569
- RFC 8609
- Git LFS API, Batch API, and Locking API documents

- [x] **Step 2: Mark draft status and risk**

Record that CCNx chunking is an Internet-Draft work in progress and FLIC is an expired Internet-Draft as of 2026-05-20; both are design references rather than normative external contracts for Project Coherent Storage.

### Task 2: Add ADR-026

**Files:**
- Create: `adr/ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics.md`
- Modify: `README.md`

- [x] **Step 1: Define the ADR decision**

Document Coherence-CE internal object chunking with immutable chunks, ordered chunk numbers, `end_chunk_number`, chunk size, chunk hashes, object manifest root, atomic manifest commit, and garbage collection.

- [x] **Step 2: Define protocol mappings**

Map S3 multipart, Git LFS OID objects, Coherence-native object API, and RAG storage chunks to the internal manifest model without changing external client protocols.

- [x] **Step 3: Define failure semantics**

Document partial upload, chunk mismatch, manifest conflict, stale reader, deletion, garbage collection, mirror lag, and backend recovery behavior.

### Task 3: Add report and OpenAPI contract

**Files:**
- Create: `reports/project-coherent-storage_coherence-ce-object-chunking-and-lfs-gateway-design.md`
- Create: `api/coherence-ce-object-chunking-lfs-gateway.openapi.yaml`
- Modify: `README.md`

- [x] **Step 1: Write gateway design report**

Describe the migration path from Gitea LFS bootstrap to Coherence-CE-backed LFS gateway, including shadow archive, validation, low-risk repo promotion, and fallback.

- [x] **Step 2: Write OpenAPI contract**

Define Coherence-native chunk/manifest endpoints and Git LFS facade endpoints for `/objects/batch`, basic upload/download actions, and lock verification.

### Task 4: Add diagrams

**Files:**
- Modify: `scripts/generate_adr_diagrams.py`
- Create: `adr/diagrams/ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics.puml`
- Create: `adr/diagrams/ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics.png`
- Create: `adr/diagrams/ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics.svg`
- Create: printable section diagrams for ADR-026

- [x] **Step 1: Add full workflow diagram**

Model external client protocols, object gateway, chunker, manifest commit, Coherence-CE placement, OpenZFS substrate, and verification.

- [x] **Step 2: Add printable diagram sections**

Create print sections for protocol mapping, manifest commit, and validation/failure semantics.

### Task 5: Validate, commit, and push

**Files:**
- All changed files

- [x] **Step 1: Run validations**

Run:

```bash
python3 -m py_compile scripts/generate_adr_diagrams.py scripts/validate_git_lfs_policy.py
python3 scripts/generate_adr_diagrams.py
DISPLAY= JAVA_TOOL_OPTIONS='-Djava.awt.headless=true' plantuml -checkonly adr/diagrams/ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics*.puml
DISPLAY= JAVA_TOOL_OPTIONS='-Djava.awt.headless=true' plantuml -tpng adr/diagrams/ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics*.puml
DISPLAY= JAVA_TOOL_OPTIONS='-Djava.awt.headless=true' plantuml -tsvg adr/diagrams/ADR-026_Coherence_CE_Object_Chunking_and_Manifest_Semantics*.puml
python3 scripts/validate_git_lfs_policy.py --remote-name origin
```

Expected result: all commands exit 0.

- [ ] **Step 2: Commit with Lore protocol**

Commit changed files using the repo commit protocol and push the working branch.
