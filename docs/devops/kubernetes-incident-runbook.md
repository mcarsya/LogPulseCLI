---
title: "Kubernetes Pod CrashLoopBackOff & Eviction Runbook"
author: "Site Reliability Engineering Team"
version: "3.1.2"
category: "DevOps & Infrastructure"
tags: [k8s, containers, crashloop, oom, incident]
last_updated: "2026-10-15"
status: "Active"
summary: "Standard operating procedure to triage and remediate CrashLoopBackOff and Node eviction events."
order: 10
---

# Kubernetes Incident Response: Pod Failures

When microservice pods enter `CrashLoopBackOff`, `OOMKilled`, or `Evicted` states, follow this triage procedure.

> [!WARNING]
> Do NOT blindly delete deployments without checking termination logs and persistent volume claims.

## Phase 1: Rapid Diagnosis

Execute the following commands from your privileged bastion terminal:

```bash
# 1. List failing pods in the target namespace
kubectl get pods -n production --field-selector=status.phase!=Running

# 2. Inspect exit code and termination reason
kubectl describe pod <pod-name> -n production | grep -A 10 "Last State"

# 3. Stream previous container crash logs
kubectl logs <pod-name> -n production --previous --tail=100
```

## Phase 2: Common Failure Modes & Remediation

### 1. Exit Code 137 (OOMKilled)
- **Root Cause**: Container memory consumption exceeded the cgroup hard memory limit (`resources.limits.memory`).
- **Remediation**:
  1. Verify heap dump or memory metrics in Grafana.
  2. Increase memory limit by 25-50% in GitOps repository (`values-production.yaml`).
  3. Commit and trigger automated deployment pipeline.

> [!TIP]
> For JVM applications, ensure `-XX:MaxRAMPercentage=75.0` is specified in container environment variables.

### 2. Exit Code 1 / 255 (Configuration or Database Connection Failure)
- **Root Cause**: Database migration failure, missing secret, or connection pool exhaustion.
- **Verification**:
```bash
# Check connectivity from ephemeral debug container
kubectl debug pod/<pod-name> -n production -it --image=nicolaka/netshoot
```

## Escalation Matrix

If recovery is not achieved within **15 minutes**:
1. Page the Secondary On-Call SRE.
2. Divert upstream edge traffic via Cloudflare / Envoy to fallback static maintenance page.

