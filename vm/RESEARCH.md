# pfSense VM Test Infrastructure Research

Research findings from manually installing pfSense CE 2.7.2 in QEMU, installing the REST API package, and studying config.xml for pre-seeding automation.

## Summary

**Can the REST API be fully pre-seeded via config.xml?** Yes. The entire REST API configuration including API keys (as SHA256 hashes), access lists, auth methods, and settings lives in `<installedpackages><package><conf>`. However, the REST API *package binary* (`pfSense-pkg-RESTAPI.pkg`) must still be installed separately — config.xml only carries the settings, not the package itself.

**Can pfSense auto-import config.xml at install time?** Yes, via the External Config Locator (ECL). During boot, pfSense searches FAT32 partitions for `config.xml` and copies it to `/cf/conf/config.xml`. Boot logs confirm: `"Looking for config.xml on da0s3"`.

## QEMU Setup

### Working QEMU Command (installer)

```bash
qemu-img create -f qcow2 vm/pfsense-test.qcow2 4G

qemu-system-x86_64 \
    -m 1024 \
    -enable-kvm \
    -drive file=vm/pfsense-test.qcow2,if=virtio,format=qcow2 \
    -drive file=vm/pfSense-CE-memstick-serial-2.7.2-RELEASE-amd64.img,format=raw,if=none,id=usbstick \
    -device usb-ehci \
    -device usb-storage,drive=usbstick,bootindex=0 \
    -nographic \
    -net nic,model=virtio \
    -net user,hostfwd=tcp::8443-:443,hostfwd=tcp::2222-:22
```

### Working QEMU Command (boot from disk)

```bash
qemu-system-x86_64 \
    -m 1024 \
    -enable-kvm \
    -drive file=vm/pfsense-test.qcow2,if=virtio,format=qcow2 \
    -nographic \
    -net nic,model=virtio \
    -net user,hostfwd=tcp::8443-:443,hostfwd=tcp::2222-:22
```

### Requirements

- KVM support (`-enable-kvm`) — AMD/Intel virtualization required
- 1024 MB RAM is sufficient
- 4 GB disk is sufficient for test image
- Serial memstick image (`-nographic` gives serial on stdio)
- User-mode networking with port forwards: host 8443 -> guest 443, host 2222 -> guest 22

### Boot Timing

- Install from memstick: ~3-5 minutes (mostly disk writes)
- Boot from QCOW2 to console menu: ~30-60 seconds
- Boot to API-ready: ~45-75 seconds (services need a few seconds after menu appears)

## Installer Automation (install.exp)

### Prompt Sequence

| Phase | Screen | Response | Gotchas |
|-------|--------|----------|---------|
| 1 | `Console type [vt100]:` | `xterm\r` | Must match before serial output |
| 2 | Copyright/License | `\r` (Accept) | Match on `Copyright\|Trademark\|Redistribution` |
| 3 | Install/Rescue/Recover | `\r` (Install is default) | Match on `Install.*Rescue\|Install.*pfSense` |
| 4 | Keymap selection | `\r` (default keymap) | Match on `Keymap\|keymap\|Continue with` |
| 5 | Partitioning method | `\r` (Auto ZFS is default) | Match on `Partitioning\|How would you like\|Auto.*ZFS` |
| 6 | ZFS Configuration | `T\r` (Pool Type shortcut) | Match on `ZFS Configuration\|Configure Options\|Pool Type` |
| 7 | Virtual Device Type | `\r` (stripe is default) | Match on `stripe\|Virtual Device` |
| 8 | Disk selection | `Space` then `\r` | `Space` toggles vtbd0 checkbox, `\r` confirms |
| 9 | ZFS Config (return) | `>` then `\r` | **Must match on `stripe: 1 disk`** (not the title). Use `>` shortcut for `>>> Install` — arrow keys fail due to ESC timing |
| 10 | Last Chance! | `\t` then `\r` | **NO is focused by default!** Must Tab to YES first |
| 11 | Installation progress | Wait ~5 min | `set timeout 900` — produces little serial output |
| 12 | Complete/Reboot | `\r` | Reboot is default |
| 13 | Shutdown | `\x01x` (Ctrl-A X) | Kill QEMU during reboot |

### Critical Gotchas

1. **ncurses escape sequence timing**: Sending `\033[A` (Up arrow) can be interpreted as standalone ESC (cancel) + `[A` garbage. Use letter shortcuts (`T`, `N`, `>`) instead of arrow keys.

2. **"Last Chance" defaults to NO**: The confirmation dialog focuses the NO button as a safety feature. Must send Tab before Enter to switch to YES.

3. **Phase 9 pattern matching**: Matching on `"ZFS Configuration"` matches too early (dialog title renders before menu items). Match on `"stripe: 1 disk"` instead — this only appears when the menu is fully drawn with the disk selected.

4. **Disk appears as `vtbd0`**: VirtIO block device, not `ada0` or `da0`.

## First Boot Automation (firstboot.exp)

### Prompt Sequence

| Phase | Screen | Response | Gotchas |
|-------|--------|----------|---------|
| 1 | VLAN setup? `[y\|n]` | `n\r` | Only on first boot (interface mismatch) |
| 2 | WAN interface name | `vtnet0\r` | VirtIO NIC name |
| 3 | LAN interface name | `\r` (none — single NIC) | Empty = no LAN |
| 4 | Confirm? `[y\|n]` | `y\r` | |
| 5 | Console menu | (wait) | Subsequent boots skip straight here |
| 6 | Enable SSH (option 14) | `14\r` then `y\r` or `n\r` | If already enabled, asks "disable?" — must send `n` |
| 7 | Shell (option 8) | `8\r` | Shell prompt: `[2.7.2-RELEASE][root@pfSense.home.arpa]/root:` |
| 8 | Install REST API | `pkg-static -C /dev/null add <url>\r` | Takes 10-30 seconds to download |
| 9 | Create API key | `curl -sk -u admin:pfsense -X POST https://127.0.0.1:8443/api/v2/auth/key` | Run from HOST side (port-forwarded) |
| 10 | Shutdown | `shutdown -p now\r` | |

### Critical Gotchas

1. **Shell prompt ANSI codes**: The pfSense tcsh prompt embeds ANSI escape codes between `/root` and `:`. Naive regex like `\$|#|%` or even `/root:` won't match. Use `home\\.arpa` which appears as consecutive bytes.

2. **SSH toggle ambiguity**: Option 14 shows "enable SSHD" if disabled, "disable SSHD" if already enabled. Must handle both cases.

3. **`service php-fpm restart` fails**: Returns "Cannot 'restart' php_fpm. Set php_fpm_enable to YES in /etc/rc.conf or use 'onerestart'". The REST API works anyway because the package installation already triggered a webConfigurator restart.

4. **REST API package URL**: `https://github.com/pfrest/pfSense-pkg-RESTAPI/releases/download/v2.4.3/pfSense-2.7.2-pkg-RESTAPI.pkg` (must match pfSense version exactly).

## Config.xml Analysis

### Structure Overview

```xml
<pfsense>
  <version>23.3</version>
  <system>           <!-- hostname, domain, admin user, SSH, webgui, etc. -->
  <interfaces>       <!-- WAN/LAN/OPTx definitions -->
  <filter>           <!-- firewall rules -->
  <cron>             <!-- scheduled tasks (including REST API cache refresh) -->
  <cert>             <!-- SSL certificates -->
  <installedpackages>  <!-- REST API config lives here -->
  <revision>         <!-- last change metadata -->
</pfsense>
```

### REST API Configuration (fully pre-seedable)

Location: `<installedpackages><package><conf>`

```xml
<conf>
    <enabled>enabled</enabled>
    <read_only>disabled</read_only>
    <keep_backup>enabled</keep_backup>
    <login_protection>enabled</login_protection>
    <hateoas>disabled</hateoas>
    <auth_methods>BasicAuth</auth_methods>  <!-- MUST include KeyAuth for API keys! -->
    <keys>
        <key>
            <username><![CDATA[admin]]></username>
            <hash_algo>sha256</hash_algo>
            <length_bytes>24</length_bytes>
            <hash>f34d9c78b795aeed5740426fd344698e5777e2177f481ecf405cb00f3ea700ea</hash>
        </key>
    </keys>
    <access_list>
        <item>
            <type>allow</type>
            <weight>10</weight>
            <network>0.0.0.0/0</network>
            <descr><![CDATA[Default allow all IPv4]]></descr>
        </item>
        <item>
            <type>allow</type>
            <weight>10</weight>
            <network>0::/0</network>
            <descr><![CDATA[Default allow all IPv6]]></descr>
        </item>
    </access_list>
</conf>
```

### auth_methods Bug

When creating an API key via `POST /api/v2/auth/key` with BasicAuth, the `auth_methods` field is set to `BasicAuth` only. Subsequent boots reject the API key with 401 because `KeyAuth` is not in the allowed methods.

**Fix**: The pre-seeded config.xml must set:
```xml
<auth_methods>BasicAuth,KeyAuth</auth_methods>
```

Or the firstboot script must update auth_methods after creating the key.

### API Key Hash Format

Keys are stored as SHA256 hashes of the raw key bytes:
- Raw key: `ef7b3ce5917e32840aff17a409fb6abeaaee3bef4b495fa3` (24 bytes hex = 48 chars)
- Hash: `f34d9c78b795aeed5740426fd344698e5777e2177f481ecf405cb00f3ea700ea`
- Algorithm: `sha256`

To pre-seed a known API key, compute `echo -n "<raw-key>" | sha256sum` and place the hash in config.xml.

### Admin Password

Stored as bcrypt hash at `<system><user><bcrypt-hash>`:
```
$2b$10$13u6qwCOwODv34GyCMgdWub6oQF3RX0rG7c3d3X4JvzuEmAXLYDd2
```
Default password: `pfsense`

### SSH Configuration

```xml
<system>
    <ssh>
        <enable>enabled</enable>
    </ssh>
</system>
```

### Interface Configuration

WAN-only setup (single NIC with DHCP):
```xml
<interfaces>
    <wan>
        <enable></enable>
        <if>vtnet0</if>
        <ipaddr>dhcp</ipaddr>
        <ipaddrv6>dhcp6</ipaddrv6>
    </wan>
</interfaces>
```

QEMU user-mode networking assigns 10.0.2.15 via DHCP.

### SSL Certificate

Self-signed cert at `<cert>`, referenced by `<system><webgui><ssl-certref>`. The cert is base64-encoded PEM. For a test VM, the auto-generated cert is fine.

### REST API Cron Jobs

The REST API package adds two cron entries for cache refresh:
- `AvailablePackageCache` (hourly at :12)
- `RESTAPIVersionReleasesCache` (hourly at :00)

These are at `<cron><item>` with commands pointing to `/usr/local/pkg/RESTAPI/.resources/scripts/manage.php refreshcache`.

## Minimum Pre-Seedable Config.xml

For a test VM with REST API ready, the minimum config.xml needs:

1. **System**: hostname, domain, admin user with bcrypt password hash, SSH enabled
2. **Interfaces**: WAN on vtnet0 with DHCP
3. **REST API package conf**: enabled, auth_methods including `KeyAuth`, pre-computed API key hash, access list
4. **SSL cert**: auto-generated is fine (pfSense creates one on first boot if missing)
5. **REST API cron jobs**: added by the package installer, not needed in pre-seed

**What still requires post-boot steps:**
- The REST API package binary must be installed via `pkg-static` (config.xml only stores settings, not packages)
- The cron jobs are created by the package installer

## Pre-Seeding Strategy

### Option A: ECL + pkg install (recommended)

1. Build a `golden-config.xml` with all settings pre-configured (SSH, auth_methods=BasicAuth,KeyAuth, API key hash, access list)
2. During install, inject config.xml via ECL (FAT32 partition on a virtual USB drive)
3. After first boot, install the REST API package via shell
4. The package reads its settings from the existing config.xml — no additional configuration needed

### Option B: QCOW2 snapshot

1. Run the full install + firstboot sequence once
2. Fix auth_methods in config.xml
3. Snapshot the QCOW2 as the golden image
4. For each test run, copy the snapshot and boot it

**Option B is simpler for CI** — just distribute a pre-built QCOW2 (or build it in a Nix derivation).

## Files Produced

| File | Purpose |
|------|---------|
| `vm/install.exp` | Automated ZFS installer via serial console |
| `vm/firstboot.exp` | First boot: interfaces, SSH, REST API, API key |
| `vm/extract-config.exp` | Quick boot to export config.xml |
| `vm/reference-config.xml` | Exported config for study (350 lines) |
| `vm/api-key.json` | API key creation response |
| `vm/RESEARCH.md` | This document |
| `vm/pfsense-test.qcow2` | 861 MB installed disk image (gitignored) |
