---
title: "Redis Cluster Node Failure & Hash Slot Rebalance"
author: "Data Platform Engineering"
version: "2.1.0"
category: "Database & Storage"
tags: [redis, caching, hash-slots, cluster, failover]
last_updated: "2026-09-12"
status: "Active"
summary: "Runbook for recovering failed Redis master shards and rebalancing hash slots."
order: 25
---

# Redis Cluster Recovery Runbook

When a master shard fails and the replica fails to automatically auto-promote, the Redis cluster transitions to a `FAIL` state.

> [!WARNING]
> While in `FAIL` state, all cluster keys mapped to the affected 1,365 hash slots will return `CLUSTERDOWN The cluster is down`.

## Step 1: Health Diagnostic

Connect to any active cluster node and query status:

```bash
redis-cli -h 10.0.12.10 -p 6379 cluster info
redis-cli -h 10.0.12.10 -p 6379 cluster nodes | grep fail
```

## Step 2: Manual Node Failover

If the standby replica is alive but election timed out:

```bash
# Connect directly to the standby replica
redis-cli -h 10.0.12.11 -p 6379 CLUSTER FAILOVER TAKEOVER
```

The replica will immediately usurp leadership and broadcast slot ownership to the remaining cluster nodes without waiting for consensus.

## Step 3: Hash Slot Rebalancing

If a shard is permanently lost without backup replicas:

```bash
# Reallocate orphaned slots to surviving masters
redis-cli --cluster fix 10.0.12.10:6379
```

