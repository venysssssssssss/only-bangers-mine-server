# All of Fabric 7 Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate and, only if performance is excellent, replace the active server with a fresh All of Fabric 7 world while preserving authentication and network services.

**Architecture:** Download the official AOF7 2.5.3 server package for Minecraft 1.20.1, boot it in an isolated staging directory on port 25566, and benchmark it before cutover. Cutover keeps the existing systemd service name and port, swaps only the Minecraft working tree, overlays compatible EasyAuth/game identity configuration, and leaves Playit and IPv6 proxy services untouched.

**Tech Stack:** Minecraft Java 1.20.1, Fabric loader pinned by the AOF7 server package, Fabric mods, systemd, Java 21 if required by the pack, CurseForge file 6766320.

**Spec:** User request in the conversation: AOF7 with the correct Minecraft/Fabric versions, new world, preserve EasyAuth/Playit/IPv6, assess 15-player performance, and remove the old active pack after validation.

## Global Constraints

- Use the official AOF7 server file `All of Fabric 7-Server-2.5.3.zip` (CurseForge file ID `6766320`).
- Use Minecraft `1.20.1`; do not upgrade the pack to another Minecraft version.
- Use the Fabric loader and Java requirements declared by the server package.
- Do not delete the current server tree until staging starts, loads the pack, and passes the benchmark gate.
- Keep `minecraft-ipv6-proxy.service`, `playit.service`, their configurations, and port `25565` unchanged.
- Preserve EasyAuth only when its mod metadata declares compatibility with Minecraft `1.20.1`; otherwise install the matching compatible release before cutover.
- Preserve the ten existing performance/optimization mods only when their metadata is compatible with AOF7/MC `1.20.1`; do not carry incompatible jars.
- Create a new world named `world-aof7`; do not reuse the old world data.
- Keep the current 8G heap initially; increase it only if measured memory headroom supports it.
- Benchmark staging and production with 5, 10, and 15 concurrent server-side players; reject cutover if 15 players produces sustained MSPT above 50 or recurring errors/disconnects.

---

### Task 1: Establish the exact pack and host baseline

**Files:**
- Create remotely: `/tmp/All-of-Fabric-7-Server-2.5.3.zip`
- Read remotely: `/home/venys1/minecraft/server/server.properties`, `/etc/systemd/system/minecraft.service`

**Interfaces:**
- Consumes: CurseForge file ID `6766320`.
- Produces: verified archive checksum, exact Fabric loader/Java requirements, current hardware/configuration baseline, and a preservation list.

- [ ] **Step 1: Download and inspect the official server package**

```bash
curl -fL --retry 3 -o /tmp/All-of-Fabric-7-Server-2.5.3.zip \
  https://www.curseforge.com/minecraft/modpacks/all-of-fabric-7/download/6766320/file
unzip -l /tmp/All-of-Fabric-7-Server-2.5.3.zip
sha256sum /tmp/All-of-Fabric-7-Server-2.5.3.zip
```

Expected: a valid ZIP named `All of Fabric 7-Server-2.5.3.zip`, with server files and no download HTML.

- [ ] **Step 2: Inspect the loader and mod metadata**

```bash
unzip -p /tmp/All-of-Fabric-7-Server-2.5.3.zip '**/fabric.mod.json' 2>/dev/null | head
unzip -p /tmp/All-of-Fabric-7-Server-2.5.3.zip '**/server.properties' 2>/dev/null
```

Record the declared Fabric loader, Java floor, mod count, server start script, and whether Carpet/fake-player benchmarking is available.

- [ ] **Step 3: Capture host and preservation baselines**

```bash
nproc
free -h
df -h /home/venys1/minecraft
java -version
find /home/venys1/minecraft/server -maxdepth 2 -iname '*easyauth*' -o -iname 'server.properties' -o -iname 'ops.json' -o -iname 'whitelist.json'
systemctl is-active minecraft.service minecraft-ipv6-proxy.service playit.service
systemctl is-enabled minecraft.service minecraft-ipv6-proxy.service playit.service
```

Expected: all three services active; record EasyAuth JAR/config paths and game identity files to overlay later.

### Task 2: Boot and validate AOF7 in staging

**Files:**
- Create remotely: `/home/venys1/minecraft/benchmark-aof7-20260911/`
- Create remotely: `/home/venys1/minecraft/benchmark-aof7-20260911/world-aof7/`

**Interfaces:**
- Consumes: the verified server ZIP and Task 1 preservation list.
- Produces: a clean AOF7 staging server on port `25566` with a new world and no startup errors.

- [ ] **Step 1: Extract into staging and run the pack installer**

```bash
mkdir -p /home/venys1/minecraft/benchmark-aof7-20260911
unzip -q /tmp/All-of-Fabric-7-Server-2.5.3.zip \
  -d /home/venys1/minecraft/benchmark-aof7-20260911
cd /home/venys1/minecraft/benchmark-aof7-20260911
chmod +x ./*.sh 2>/dev/null || true
./install.sh 2>/dev/null || true
```

Expected: the server launcher and all required pack files are present; any installer prompt is answered with the accepted EULA only after confirming the pack source.

- [ ] **Step 2: Apply only safe staging overrides**

```properties
server-port=25566
level-name=world-aof7
online-mode=false
max-players=15
view-distance=8
simulation-distance=6
```

Copy EasyAuth only after its metadata passes the 1.20.1 compatibility check. Copy `eula.txt`, `ops.json`, `whitelist.json`, and ban lists only when their formats are accepted by 1.20.1.

- [ ] **Step 3: Start staging and inspect the first boot**

```bash
systemd-run --user --unit=aof7-staging --working-directory=/home/venys1/minecraft/benchmark-aof7-20260911 \
  /usr/bin/java -Xms8G -Xmx8G -XX:+UseG1GC -jar <launcher-from-package> nogui
```

Expected: staging reaches `Done`, creates `world-aof7`, listens on `25566`, and logs no mod resolution, mixin, or authentication failures.

### Task 3: Measure the AOF7 capacity gate

**Files:**
- Create remotely: `/home/venys1/minecraft/benchmark-aof7-20260911/benchmark-results/`

**Interfaces:**
- Consumes: the running staging server from Task 2.
- Produces: repeatable 5/10/15-player results with MSPT, CPU, memory, disconnects, errors, and world-generation observations.

- [ ] **Step 1: Confirm the measurement path**

Use Carpet fake players if the pack contains Carpet; otherwise use the existing benchmark runner’s smallest available native protocol client. Run one 5-player smoke test and verify all joins are counted.

- [ ] **Step 2: Run three repetitions at each load**

```text
players: 5, 10, 15
repetitions: 3 each
warmup: 60 seconds
measurement: 300 seconds
```

Keep all players inside the pre-rendered/stable area for the first gate, then run one exploration pass to expose chunk-generation cost.

- [ ] **Step 3: Apply the performance gate**

Accept only if the 15-player group has median MSPT below `20 ms`, no sustained sample above `50 ms`, zero unexpected disconnects, zero repeated mod errors, and CPU/RAM remain below the host’s safe headroom. Treat isolated P99 spikes as warnings, not a pass by themselves.

### Task 4: Cut over without losing functional services

**Files:**
- Preserve remotely: `/home/venys1/minecraft/server-old-20260911/`
- Replace remotely: `/home/venys1/minecraft/server/`
- Leave unchanged: `/etc/systemd/system/minecraft-ipv6-proxy.service`, `/etc/systemd/system/playit.service`, and their configs

**Interfaces:**
- Consumes: a passing staging benchmark and the preservation list.
- Produces: the active AOF7 server on port `25565`, new world `world-aof7`, preserved EasyAuth/game identity settings, and unchanged network services.

- [ ] **Step 1: Stop Minecraft cleanly and snapshot the old tree**

```bash
sudo systemctl stop minecraft.service
mv /home/venys1/minecraft/server /home/venys1/minecraft/server-old-20260911
```

Verify the process exited before continuing; do not touch the IPv6 proxy or Playit service.

- [ ] **Step 2: Promote the validated staging tree**

```bash
mv /home/venys1/minecraft/benchmark-aof7-20260911 /home/venys1/minecraft/server
```

Overlay only the preserved compatible files, set `server-port=25565`, keep `level-name=world-aof7`, and install the validated `server-icon.png`.

- [ ] **Step 3: Remove obsolete active-pack files after promotion**

Delete only the old tree’s obsolete modpack/Fabric runtime files after the new service boots and passes post-cutover checks; retain a dated backup of world/config data until the user confirms rollback is no longer needed.

- [ ] **Step 4: Start the production service**

```bash
sudo systemctl start minecraft.service
systemctl is-active minecraft.service minecraft-ipv6-proxy.service playit.service
```

Expected: all three services are active and Minecraft listens on `25565`.

### Task 5: Verify production behavior and hand off

**Files:**
- Read remotely: `/home/venys1/minecraft/server/logs/latest.log`
- Create remotely: `/home/venys1/minecraft/benchmark-results-aof7-20260911/`

**Interfaces:**
- Consumes: the active AOF7 service from Task 4.
- Produces: final health report and rollback point.

- [ ] **Step 1: Verify version, world, auth, and network**

Confirm logs show Minecraft `1.20.1`, the expected Fabric loader, world `world-aof7`, EasyAuth initialization, the compatible optimization mods, port `25565`, IPv6 proxy active, and Playit active.

- [ ] **Step 2: Re-run the 15-player production smoke test**

Run the 5/10/15 player matrix’s shortest smoke pass; abort if errors, disconnects, or sustained MSPT regress.

- [ ] **Step 3: Keep rollback available**

The rollback is `sudo systemctl stop minecraft.service`, swap `server` with `server-old-20260911`, then `sudo systemctl start minecraft.service`; do not delete the backup until the new server is accepted.

---

## Self-review

- CurseForge version, server file, Minecraft version, and Fabric loader are covered by Tasks 1–2.
- Capacity evaluation, new world, and 5/10/15-player benchmarks are covered by Task 3.
- EasyAuth, Playit, IPv6, port preservation, old-pack removal, and rollback are covered by Task 4.
- Production verification and rollback evidence are covered by Task 5.
- No step depends on an untracked placeholder: the launcher name and exact Fabric loader are read from the downloaded package before launch.
