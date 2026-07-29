# Templates and Verification

## Intake Template

```text
Audience/persona:
Deliverable and publishing surface:
Requested Tech:Marketing dial or preset:
Source material and approved claims:
Required terminology:
Required call to action:
Constraints, risks, or prohibited claims:
```

## Optional Editorial Report Template

Use this only when the user explicitly requests an editorial report. Keep it outside the requested document. Never append it to a document being drafted or edited by default.

```markdown
> **Executive Balance Summary**
> - **Applied dial:** `80:20`
> - **Audience and deliverable:** `Platform engineers; README`
> - **Editorial choices:** Technical setup leads; the opening states the supported workflow and intended user.
> - **Validation required:** `[Validate: supported Kubernetes versions.]`
```

## Verification Case 1: Rust Library README — 80:20

**Prompt:** `Write a README for a Rust crate that validates signed webhook payloads. Use the supplied Cargo.toml, public API docs, and test fixture. Aim for 80:20.`

**Expected processing:** Read the precision reference. Use the marketing engine only for a short opening that identifies Rust services receiving signed webhooks. Provide prerequisites, `Cargo.toml` dependency, a complete verification example, expected success/failure behavior, authentication/key handling, and links to verified API docs. Flag any performance or compatibility claim not present in the sources.

**Pass condition:** A developer can run the example after replacing placeholders; prose does not call the crate secure or robust without evidence.

## Verification Case 2: SaaS Launch Post — 20:80

**Prompt:** `Draft a launch post for a feature that lets platform teams preview Terraform plan changes in pull requests. Use these approved quotes and metrics. Aim for 20:80.`

**Expected processing:** Read the marketing reference and use the precision reference only for implementation facts. Lead with the review bottleneck, explain the capability and changed workflow, include only supplied metrics, show one accurate technical detail, and finish with a low-commitment CTA.

**Pass condition:** Narrative leads, but technical capabilities and metrics are traceable to supplied evidence; no generic superlatives appear.

## Verification Case 3: API Error Handling Guide — 100:0

**Prompt:** `Document how clients should handle 401, 403, 409, 429, and 5xx responses for this API. Use the OpenAPI document and retry policy. Aim for 100:0.`

**Expected processing:** Read the precision reference. Organize by status code with condition, evidence, action, retry safety, and escalation condition. Use only documented headers, error fields, and backoff rules. Do not add a CTA, positioning, or promotional introduction.

**Pass condition:** Every action is deterministic or explicitly conditioned; unknown retry/idempotency details remain marked for validation.
