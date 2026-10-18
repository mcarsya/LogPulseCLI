---
title: "CI/CD Pipeline Security & Secret Hygiene Policy"
author: "Information Security Guild"
version: "1.8.0"
category: "DevOps & Infrastructure"
tags: [security, cicd, secrets, compliance, audit]
last_updated: "2026-09-28"
status: "Active"
summary: "Mandatory corporate guidelines for container image scanning, signing, and secret segregation."
order: 15
---

# CI/CD Pipeline Security Standards

All delivery pipelines across the enterprise must adhere to zero-trust principles and verifiable artifact provenance.

> [!IMPORTANT]
> Hardcoding credentials, API tokens, or SSH keys in source control repositories will trigger automated Git pre-commit rejection and revoke access tokens immediately.

## Mandatory Pipeline Gates

Every pull request must pass the four compliance gates before merge eligibility:

1. **Static Application Security Testing (SAST)**: Zero high/critical vulnerabilities.
2. **Software Bill of Materials (SBOM)**: CycloneDX JSON artifact generation.
3. **Container Image Scanning (Trivy/Grype)**: Vulnerability cutoff threshold: `CVSS >= 7.0`.
4. **Cosign Cryptographic Image Signing**: Sign images with corporate KMS key.

```bash
# Example verification command
cosign verify --key awskms:///arn:aws:kms:us-east-1:123456789:key/corporate-signing-key \
  registry.internal.corp/production/payment-gateway:v2.4.0
```

> [!NOTE]
> Audit logs for all deployments are retained for 365 days and ingested into the LogPulse audit pipeline for quarterly compliance reviews.

