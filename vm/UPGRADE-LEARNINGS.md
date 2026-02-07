# pfSense 2.7.2 → 2.8.1 Upgrade Learnings

## The Problem

pfSense 2.7.2 ships with `pfSense-upgrade` which calls `pfSense-repo-setup` which calls `pfSense-repoc-static`. The upgrade toolchain is designed for Netgate's official upgrade path and fights manual repo switching at every step.

## What Failed

### Attempt 1: Edit config.xml + sed repo conf in-place

```
sed -i '' 's|pfSense_v2_7_2|pfSense_v2_8_1|g' pfSense-repo-2.7.2.conf
```

**Result**: `pfSense-upgrade -y` fetched 550 packages from the 2.8.1 repo but reported "Your packages are up to date". The repo URLs were correct but the ABI mismatch (`FreeBSD:14` vs `FreeBSD:15`) caused pkg to silently filter out all packages as incompatible.

### Attempt 2: Copy 2_8_1.abi over 2.7.2.abi

Copied the `FreeBSD:15:amd64` ABI file but `pkg.conf` still had `ABI=FreeBSD:14:amd64`. The `.abi` file is only read by `pfSense-repo-setup`'s `abi_setup()` function, not by `pkg-static` directly. `pkg-static` reads `pkg.conf`.

### Attempt 3: Set config.xml `pkg_repo_conf_path` to `2_8_1`

```xml
<pkg_repo_conf_path>2_8_1</pkg_repo_conf_path>
```

**Result**: `pfSense-repo-setup` calls `get_repo_name("2_8_1")` which strips `.conf` → looks for `"2_8_1.name"` (relative path) → file doesn't exist → returns empty → falls back to the default 2.7.2 repo. The value must be a **full absolute path** to a `.conf` file.

### Attempt 4: REST API v2.7.1 pkg install on FreeBSD 14

```
pkg-static -C /dev/null add pfSense-2.8.1-pkg-RESTAPI.pkg
```

**Result**: `wrong architecture: FreeBSD:15:* instead of FreeBSD:14:amd64`. The REST API v2.7.1 package is compiled for FreeBSD 15 (pfSense 2.8.1) and won't install on FreeBSD 14 (pfSense 2.7.2). The upgrade must complete first.

### Attempt 5: `pfSense-upgrade -d -c` with env vars

```
env ABI=FreeBSD:15:amd64 IGNORE_OSVERSION=yes pfSense-upgrade -d -c
```

**Result**: "Major OS version upgrade detected" warning but still "up to date". The `ABI` env var doesn't override `pkg.conf` — pkg reads the config file, not the environment.

### Attempt 6: Option 13 "Update from console"

**Result**: Same "up to date" — it just calls `pfSense-upgrade` internally.

## What Works

### The proven fix sequence (from explore-upgrade.exp)

These three steps were validated to make `pkg-static` see the 2.8.1 packages:

#### Step 1: Override `pkg.conf` ABI

```sh
printf 'ABI=FreeBSD:15:amd64\nALTABI=freebsd:15:x86:64\n' > /usr/local/etc/pkg.conf
```

This is the **only way** to change what ABI `pkg-static` uses. Environment variables don't work. The `.abi` files in the repo dir are only used by `pfSense-repo-setup`, not by pkg directly.

#### Step 2: Force the symlink to 2_8_1.conf

```sh
ln -sf /usr/local/etc/pfSense/pkg/repos/pfSense-repo-2_8_1.conf /usr/local/etc/pkg/repos/pfSense.conf
```

The `pfSense-repo-2_8_1.conf` file **already exists** on stock pfSense 2.7.2 with the correct 2.8.1 URLs:
```
pfSense-core: { url: "pkg+https://pkg.pfsense.org/pfSense_v2_8_1_amd64-core" }
pfSense:      { url: "pkg+https://pkg.pfsense.org/pfSense_v2_8_1_amd64-pfSense_v2_8_1" }
```

#### Step 3: Set IGNORE_OSVERSION=yes

```sh
setenv IGNORE_OSVERSION yes   # tcsh
export IGNORE_OSVERSION=yes   # sh/bash
```

**CRITICAL**: Without this, `pkg-static update -f` hangs on an interactive prompt:
```
Newer FreeBSD version for package whois:
To ignore this error set IGNORE_OSVERSION=yes
- package: 1500029
- running kernel: 1400094
Ignore the mismatch and continue? [y/N]:
```

This prompt repeats for every subsequent pkg command, eating all input. The exploration run got stuck here — every command sent after was interpreted as a response to `[y/N]`.

#### After those three steps

```sh
pkg-static clean -ay
pkg-static update -f         # fetches 2.8.1 package catalogs
pkg-static install -fy pkg pfSense-repo pfSense-upgrade  # updates the upgrade toolchain
pfSense-upgrade -U -y        # -U skips pfSense-repoc-static
```

## Key Source Code Findings

### `pfSense-repo-setup` (shell script at `/usr/local/sbin/pfSense-repo-setup`)

```
main():
  PKG_REPO_CONF_PATH = read_xml_tag("system/pkg_repo_conf_path")
  if empty: PKG_REPO_CONF_PATH = get_default_repo()   # finds *.default file
  validate_repo_conf()                                  # resolves .name file
  pfSense_repo_setup():
    if not NOUPDATE: pfSense-repoc-static               # contacts ews.netgate.com
    validate_repo_conf()                                # may reset symlink!
    abi_setup()                                         # writes pkg.conf from .abi file
```

- `get_repo_name(path)`: strips `.conf`, appends `.name`, reads file content. Returns empty if `.name` doesn't exist.
- `validate_repo_conf()`: constructs `pfSense-repo-${repo_name}.conf`, checks if it exists. If not, falls back to default. Then **resets the symlink** to point to the resolved conf.
- `abi_setup()`: reads `.abi` file from the resolved repo conf path, writes `ABI=` to `pkg.conf`. Returns exit code 12 for NEW_MAJOR.
- `-U` flag sets `NOUPDATE=1`, skipping `pfSense-repoc-static`.

### `pfSense-upgrade` (shell script at `/usr/local/libexec/pfSense-upgrade`)

```
-U flag: sets dont_update=" -U", passed to pfSense-repo-setup
-y flag: sets yes=1, auto-confirms prompts

Line 2280: /usr/local/sbin/${product}-repo-setup ${dont_update}
Exit codes from repo-setup:
  12 → NEW_MAJOR=1, IGNORE_OSVERSION=yes  (this is what we want!)
  13 → reinstall_pkg + NEW_MAJOR
  1  → "failed to update repository settings!!!" exit

Then: pkg_upgrade() → check_upgrade → compare_pkg_version → "up to date" or upgrade
```

### `pfSense-repoc-static` (binary)

- Contacts `ews.netgate.com` to fetch branch/repo data
- In QEMU VMs: completes with exit code 0 but returns 2.7.2 branch data (no hardware serial)
- When it runs, it can **reset repo config files**, undoing manual edits
- `-U` flag to `pfSense-repo-setup` skips it entirely

## Repo File Inventory (stock pfSense 2.7.2)

```
/usr/local/etc/pfSense/pkg/repos/
├── pfSense-repo-2.7.2.abi        # "FreeBSD:14:amd64"
├── pfSense-repo-2.7.2.altabi     # "freebsd:14:x86:64"
├── pfSense-repo-2.7.2.conf       # URLs: pfSense_v2_7_2_amd64-*
├── pfSense-repo-2.7.2.default    # marks 2.7.2 as default (empty file)
├── pfSense-repo-2.7.2.descr      # "pfSense CE 2.7.2-RELEASE repo"
├── pfSense-repo-2.7.2.name       # "2.7.2" (content of file)
├── pfSense-repo-2_8_1.abi        # "FreeBSD:15:amd64"
├── pfSense-repo-2_8_1.altabi     # "freebsd:15:x86:64"
├── pfSense-repo-2_8_1.conf       # URLs: pfSense_v2_8_1_amd64-*
├── pfSense-repo-2_8_1.descr      # description
└── pfSense-repo-2_8_1.name       # "2_8_1" (content of file)

/usr/local/etc/pkg/repos/pfSense.conf → symlink to pfSense-repo-2.7.2.conf
/usr/local/etc/pkg.conf             → "ABI=FreeBSD:14:amd64\nALTABI=freebsd:14:x86:64"
```

Note: 2_8_1 has NO `.default` file. The `.default` file marks which repo is the fallback.

## Shell Gotchas

- pfSense uses **tcsh**, not bash. `for` loops, `export`, heredocs all fail. Use `setenv`, `printf`, simple commands.
- `2>&1` redirect fails in tcsh ("Ambiguous output redirect"). Use `command >& file` or pipe to a file.
- FreeBSD `sed -i` requires `sed -i ''` (explicit empty backup suffix). Without `''` it treats the next argument as the backup suffix.
- `IGNORE_OSVERSION=yes command` syntax doesn't work in tcsh. Must `setenv` first.
- `pkg bootstrap -f` was suggested by warning messages but never tested — may be another viable approach.

## Timing

- Install from memstick: ~3-5 min
- First boot + REST API install: ~2-3 min
- Post-firstboot snapshot save: ~30 sec
- Upgrade (download + install + reboot): ~15 min (estimated, not yet completed)
- Boot to API-ready after upgrade: ~60-90 sec
