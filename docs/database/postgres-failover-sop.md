---
title: "PostgreSQL High-Availability Failover SOP"
author: "Data Platform Engineering"
version: "4.0.1"
category: "Database & Storage"
tags: [postgres, patroni, failover, disaster-recovery, database]
last_updated: "2026-10-10"
status: "Active"
summary: "Procedures for promoting standby replicas and resolving split-brain scenarios using Patroni."
order: 20
---

# PostgreSQL Primary Promotion & Standby Recovery

In the event of unrecoverable hardware failure on the primary PostgreSQL cluster node, Patroni orchestrates leader election via DCS (etcd/Consul).

> [!CAUTION]
> Manual promotion bypasses DCS consensus and can cause split-brain data corruption. Only perform manual promotion if DCS is completely unreachable.

## Automated Failover Inspection

To check current cluster topology and replication lag:

```bash
# Verify Patroni cluster status
patronictl -c /etc/patroni/production.yml topology

# Check streaming replication lag
SELECT client_addr, state, sync_state, 
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_bytes 
FROM pg_stat_replication;
```

## Controlled Switchover Procedure

When performing scheduled maintenance on the active leader:

1. Confirm all replicas have `lag_bytes == 0`.
2. Execute graceful switchover:
   ```bash
   patronictl -c /etc/patroni/production.yml switchover --master pg-node-01 --candidate pg-node-02
   ```
3. Monitor application connection pools (PgBouncer) for reconnection within 3 seconds.
4. Verify read/write traffic is accepted on the new leader node.

> [!TIP]
> Always run an index health check (`pg_stat_user_indexes`) after a major failover event to ensure replication stream fidelity.

