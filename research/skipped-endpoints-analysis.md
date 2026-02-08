# Unblocking 16 pfSense REST API test endpoints

**Of the 16 skipped endpoints, 10 can be unblocked with concrete workarounds, 3 require infrastructure additions (Pebble container or second VM), and 3 should remain skipped as by-design limitations or too-risky operations.** The root causes span framework bugs in parent model construction, nginx timeout constraints, content negotiation gaps, and singleton design patterns. Below is a category-by-category analysis with exact remediation steps, drawn from the pfrest source architecture, GitHub issues, and pfSense documentation.

---

## 1. HAProxy sub-resources fail on parent model construction

**Endpoints:** `POST /api/v2/services/haproxy/settings/dns_resolver`, `POST /api/v2/services/haproxy/settings/email_mailer`

**Root cause:** The `HAProxyDNSResolver` and `HAProxyEmailMailer` models declare `parent_model_class = 'HAProxySettings'`. HAProxySettings is a singleton (`many=false`), so the framework auto-resolves it without needing a `parent_id`. However, the Model base class constructs the parent by reading its `config_path` from config.xml. If HAProxy's config section (typically `installedpackages/haproxy`) doesn't exist in config.xml, the parent construction fails with `MODEL_CANNOT_GET_CONFIG_PATH_WITHOUT_PARENT_MODEL`. This is the same class of bug that caused issues #764 (REST API settings page crash from "unnecessary initialization of certain models") and #781 (DHCPServer unintentional initialization), both fixed in v2.6.5.

**No GitHub issue exists** for this specific HAProxy sub-resource bug. The closest related issues are #681 (DNS resolver settings with pfBlockerNG, a different `FIELD_CHOICES_CALLABLE_NOT_FOUND` error) and the parent model initialization bugs above.

**Workaround approach — initialize HAProxy config via the GUI, then re-test:**

1. Open the pfSense web GUI at **Services -> HAProxy -> Settings**
2. Configure at least one setting (e.g., set Max Connections to `256`) and click Save
3. This creates the `installedpackages/haproxy` section in config.xml
4. Now attempt `POST /api/v2/services/haproxy/settings/dns_resolver` again

If the user already tried `PATCH /api/v2/services/haproxy/settings` and it didn't work, the PATCH itself may fail for the same reason — the framework tries to read the parent config path before the PATCH can create it. The **GUI initialization is the more reliable path** because it writes directly to config.xml. Alternatively, use the `POST /api/v2/diagnostics/command_prompt` endpoint to manually inject the config:

```json
{
  "shell_cmd": "php -r \"require_once('config.inc'); init_config_arr(array('installedpackages', 'haproxy')); write_config('Initialize HAProxy config');\""
}
```

After this, PATCH the parent settings to populate it, then POST the sub-resources.

**Confidence:** Medium. The config initialization should resolve the parent construction error, but the user reports trying PATCH already. If it still fails after GUI/shell initialization, this is likely a deeper framework bug that needs an upstream fix. **File a GitHub issue** referencing the `MODEL_CANNOT_GET_CONFIG_PATH_WITHOUT_PARENT_MODEL` error with HAProxy sub-resources.

### Sprint 4 Result: BLOCKED

Tried the PHP init approach via `diagnostics/command_prompt`:

```json
{"shell_cmd": "php -r \"require_once('config.inc'); init_config_arr(array('installedpackages', 'haproxy')); $config['installedpackages']['haproxy']['enableoption'] = 'yes'; write_config('Initialize HAProxy config');\""}
```

**Results:** CREATE (POST) returns 200 after config.xml initialization — the sub-resources can be created. However, GET and DELETE both fail with the same `MODEL_CANNOT_GET_CONFIG_PATH_WITHOUT_PARENT_MODEL` error. The bug is inconsistent: POST uses a different code path that can construct the parent model, but GET/DELETE cannot. This appears to be a genuine framework bug where the Model base class fails to re-resolve the singleton parent during read/delete operations even when the config.xml section exists.

**Decision:** Stays skipped. This is a confirmed REST API v2.7.1 framework bug. CREATE works but GET/DELETE are broken, making the endpoint unusable for full CRUD. The `delete_may_fail` pattern was prototyped but doesn't add real test value since we can't verify the created resource.

---

## 2. PKCS12 export requires the right Accept header

**Endpoint:** `POST /api/v2/system/certificate/pkcs12/export`

**Root cause:** The pfrest framework has three ContentHandler classes: `JSONContentHandler` (`application/json`), `URLContentHandler` (`application/x-www-form-urlencoded`), and **`BinaryContentHandler` (`application/octet-stream`)**. Each Endpoint class declares which ContentHandlers it supports for encoding responses via `$encode_content_handlers`. The PKCS12 export endpoint almost certainly only lists `BinaryContentHandler` for encoding (since the output is raw PKCS12 binary), which means `Accept: application/json` and `Accept: */*` both return **406** because the content negotiation requires an exact MIME type match.

Discussion #388 on GitHub (titled "Handling of private key in Certificate API") explicitly discusses PKCS12 export binary handling. A contributor proposed return ID 16 for `application/octet-stream` responses with the message "Download file of type application/octet-stream." This architecture was incorporated into v2's `BinaryContentHandler`.

**Workaround — send the correct Accept header:**

```bash
curl -X POST \
  -H "Accept: application/octet-stream" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"id": "CERT_REFID", "encryption": "high", "passphrase": "test123"}' \
  https://pfsense/api/v2/system/certificate/pkcs12/export \
  --output cert.p12
```

If `Accept: application/octet-stream` still returns 406, the endpoint may have an empty or misconfigured `$encode_content_handlers` array — a genuine bug. In that case, use this **fallback workaround** that exports the cert and key separately and builds PKCS12 client-side:

```bash
# Get cert data (includes crt and prv fields in base64)
CERT_DATA=$(curl -s -H "X-API-Key: YOUR_KEY" \
  https://pfsense/api/v2/system/certificate?id=REFID)

# Extract and decode cert/key, then build PKCS12 locally
echo "$CERT_DATA" | jq -r '.data.crt' | base64 -d > cert.pem
echo "$CERT_DATA" | jq -r '.data.prv' | base64 -d > key.pem
openssl pkcs12 -export -in cert.pem -inkey key.pem -out cert.p12 -passout pass:test123
```

**Confidence:** Medium for the `Accept: application/octet-stream` fix (the infrastructure exists but may not be wired to this endpoint). High for the client-side PKCS12 generation workaround.

### Sprint 3 Result: DONE

The `Accept: application/octet-stream` header works perfectly. This was never a bug — just incorrect content negotiation on our side. The previous test sent `Accept: */*` which returns 406 because pfrest's `BinaryContentHandler` requires an exact MIME type match. With the correct header, the endpoint returns raw PKCS12 binary data with status 200.

**Test added:** `test_action_system_certificate_pkcs12_export` — generates CA + cert, exports as PKCS12 with `Accept: application/octet-stream`, asserts 200 and non-empty response body. Cleanup deletes cert and CA. Works on both v2.4.3 and v2.7.1.

**Decision:** Unblocked. The fallback workaround (client-side PKCS12 generation) was never needed.

---

## 3. Package install timeouts can be sidestepped entirely

**Endpoints:** `POST /api/v2/system/package`, `DELETE /api/v2/system/package`

**Root cause:** pfSense's nginx uses a **hardcoded 60-second `fastcgi_read_timeout`** that cannot be changed via the API or config.xml. Package operations routinely take 90-180 seconds. The REST API's nginx hook (`restapi_plugin_nginx()`) adds HTTP method support but does not override timeouts. Issue #779 confirms the same 504 pattern for user group updates, and pfSense core bugs #6396 and #11583 document this as an intentional limit.

The REST API v2 does have a **Dispatcher framework** for async operations with a 300-second default timeout and a `max_queue` of 10. Endpoints can accept an `async` parameter where `async=true` (the default) runs operations in the background. However, even the initial request to spawn a Dispatcher may exceed 60 seconds if the model performs synchronous package operations before dispatching.

**Best workaround — pre-install packages in the golden VM image:**

```bash
# SSH into pfSense before creating the VM snapshot:
pkg install -y pfSense-pkg-haproxy pfSense-pkg-openvpn-client-export pfSense-pkg-acme
```

This eliminates the need to test package install at all. For test coverage of the endpoint itself, use the **504-as-success pattern**:

```python
import requests, time

try:
    resp = requests.post(
        "https://pfsense/api/v2/system/package",
        json={"name": "pfSense-pkg-cron"},
        headers={"X-API-Key": KEY},
        timeout=120, verify=False
    )
except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
    pass  # Expected — the operation continues in background

# Poll for completion
for _ in range(30):
    time.sleep(10)
    check = requests.get(
        "https://pfsense/api/v2/system/package",
        headers={"X-API-Key": KEY}, verify=False
    )
    packages = check.json().get("data", [])
    if any(p.get("name") == "pfSense-pkg-cron" for p in packages):
        break  # Package installed successfully
```

A small, fast-installing package like `pfSense-pkg-cron` may complete within the 60-second window. The deletion of that same small package is also fast enough to succeed.

**Confidence:** High for pre-install approach. Medium-high for the 504-polling pattern with a small package.

### Sprint 5 Result: BLOCKED

Attempted the 504-polling pattern with `pfSense-pkg-cron`. The POST returned 404 with `FOREIGN_MODEL_FIELD_VALUE_NOT_FOUND` — the package `pfSense-pkg-cron` does not exist in the pfSense 2.8.1 package repository. The actual package name in the repo is `pfSense-pkg-Cron` (capital C), which is already pre-installed in our golden image.

Even with a valid uninstalled package, the approach is inherently flaky: QEMU NAT is slow/unreliable for package downloads, and nginx's hardcoded 60s `fastcgi_read_timeout` means the test would depend on package download speed. The GET endpoints (`/api/v2/system/package` and `/api/v2/system/package/available`) are already tested via read-only tests.

**Decision:** Stays skipped. The 504-polling pattern is too fragile for CI. GET endpoints are already covered. Package install/delete should only be tested manually with a direct network connection.

---

## 4. Interface CRUD is safe with VLANs on the spare NIC

**Endpoints:** `POST /api/v2/interface`, `PATCH /api/v2/interface`, `DELETE /api/v2/interface`

**Root cause:** Not a bug — the skip is a safety precaution. The `/api/v2/interface` endpoint creates pfSense interface assignments (mapping a physical/virtual NIC like `em2.100` to a logical slot like `opt1`). This is equivalent to Interfaces -> Assignments -> Add in the GUI.

**The key insight is that VLAN sub-interfaces on the spare NIC (em2) are completely safe to create and destroy** without affecting em0 (WAN) or em1 (LAN). A VLAN is a logical construct that never modifies the parent physical interface.

**Safe test sequence:**

```bash
# Step 1: Create VLAN on spare NIC
POST /api/v2/interface/vlan
{"if": "em2", "tag": 999, "descr": "TestVLAN", "pcp": 0}
# Returns: VLAN ID (e.g., id=0)

# Step 2: Assign VLAN as new pfSense interface
POST /api/v2/interface
{"if": "em2.999", "descr": "TESTVLAN", "enable": true,
 "typev4": "static", "ipaddr": "10.99.99.1", "subnet": "24"}
# Returns: interface ID (e.g., "opt1")

# Step 3: Verify with PATCH
PATCH /api/v2/interface
{"id": "opt1", "descr": "TESTVLAN_UPDATED"}

# Step 4: Apply changes
POST /api/v2/interface/apply

# Step 5: Clean up — delete interface assignment
DELETE /api/v2/interface
{"id": "opt1"}

# Step 6: Clean up — delete VLAN
DELETE /api/v2/interface/vlan
{"id": 0}

# Step 7: Apply again
POST /api/v2/interface/apply
```

Note that issue #536 (fixed in v2.1.0) previously caused the API to miss VLAN and GIF interfaces during enumeration, but this is resolved in v2.7.1. Also, issue #162 documents gateway timeouts when applying changes with bridge interfaces — avoid creating bridge interfaces in tests.

**Confidence:** High. VLANs on a spare NIC are a standard, well-tested pattern for interface testing.

### Sprint 1 Result: DONE

The VLAN-on-em2 approach works exactly as described. Added as a `_CHAINED_CRUD` entry with one parent (VLAN on em2, tag 999) that injects its `vlanif` field (`em2.999`) as the child interface's `if` field.

**Test added:** `test_crud_interface` — creates VLAN parent (em2:999), assigns as interface with static IPv4 (10.99.99.1/24), tests GET and PATCH (descr update), then cleans up interface and VLAN in reverse order. No collision with existing VLAN test (which uses em0:100) or LAGG test (which uses bare em2).

**Decision:** Unblocked. The safety concern was overly conservative — VLAN on a spare NIC is completely isolated from WAN/LAN.

---

## 5. OpenVPN client export works with a 6-step setup chain

**Endpoints:** `POST /api/v2/vpn/openvpn/client_export`, `GET /api/v2/vpn/openvpn/client_export/config`, `DELETE /api/v2/vpn/openvpn/client_export/config`

**Root cause:** Not a bug — just complex dependencies. The `openvpn-client-export` package must be installed, and a full OpenVPN server + CA + certificates chain must exist. The feature was added in v2.6.0 (issue #368), with bug fixes in v2.6.4 (#756 — cert location) and v2.6.7 (#798 — proxy attributes).

**Pre-requisite:** The `pfSense-pkg-openvpn-client-export` package must be installed. **Pre-install it in the golden image** to avoid the 504 timeout issue from Category 3.

**Complete API call sequence:**

```bash
# 1. Create CA
POST /api/v2/system/ca
{"descr": "TestCA", "method": "internal", "trust": true,
 "keytype": "RSA", "keylen": 2048, "digest_alg": "sha256",
 "lifetime": 3650, "dn_commonname": "TestCA",
 "dn_country": "US", "dn_state": "CA", "dn_city": "Test",
 "dn_organization": "Test"}
# Save: $CA_REFID from response

# 2. Create server certificate
POST /api/v2/system/certificate
{"descr": "VPNServerCert", "method": "internal",
 "caref": "$CA_REFID", "keytype": "RSA", "keylen": 2048,
 "digest_alg": "sha256", "lifetime": 3650, "type": "server",
 "dn_commonname": "vpnserver.test.local"}
# Save: $SERVER_CERT_REFID

# 3. Create OpenVPN server
POST /api/v2/vpn/openvpn/server
{"mode": "server_tls", "protocol": "UDP4", "dev_mode": "tun",
 "interface": "wan", "local_port": 1194,
 "caref": "$CA_REFID", "certref": "$SERVER_CERT_REFID",
 "dh_length": 2048, "tunnel_network": "10.0.8.0/24",
 "description": "TestVPN"}
# Save: $VPNID

# 4. Create user certificate
POST /api/v2/system/certificate
{"descr": "UserCert", "method": "internal",
 "caref": "$CA_REFID", "keytype": "RSA", "keylen": 2048,
 "digest_alg": "sha256", "lifetime": 365, "type": "user",
 "dn_commonname": "testuser"}
# Save: $USER_CERT_REFID

# 5. Export client config (the actual test)
POST /api/v2/vpn/openvpn/client_export
{"vpnid": $VPNID, "certref": "$USER_CERT_REFID"}

# 6. GET and DELETE the export config
GET /api/v2/vpn/openvpn/client_export/config?vpnid=$VPNID
DELETE /api/v2/vpn/openvpn/client_export/config
```

Use `mode: "server_tls"` (TLS only, no user auth) to avoid issue #561, where `authmode: ["Local Database"]` caused a 404 because the API couldn't resolve the auth server name. The minimum OpenVPN server config requires: `mode`, `protocol`, `dev_mode`, `interface`, `local_port`, `caref`, `certref`, `tunnel_network`, and `description`.

**Confidence:** High. This is well-documented, actively maintained, and has test cases in the repo's own test suite (`APIModelsOpenVPNClientExportTestCase.inc`).

### Sprint 6 Result: DONE

Successfully implemented as a custom test with a 7-step chain (one more step than the research predicted). Key learnings:

1. **`local_port` must be a string**, not integer — the API returns `FIELD_INVALID_TYPE` otherwise.
2. **`ecdh_curve` is required** — not mentioned in the research's minimal config. Must include `"ecdh_curve": "prime256v1"`.
3. **`server_tls` mode produces log output before JSON** — the OVPN server creation response includes `"Starting DNS Resolver..."` prefixed to the JSON body. Parsed with `text.find("{")` to skip the prefix.
4. **The research's call sequence is wrong** — `POST /api/v2/vpn/openvpn/client_export` does NOT create an export from scratch. It requires an existing `client_export/config` object (created via `POST /api/v2/vpn/openvpn/client_export/config`). The correct sequence is:
   - Create CA → server cert → OVPN server → user cert → **export config** → export
5. **Export config POST requires many fields** — `server`, `pkcs11providers`, `pkcs11id`, `pass`, `proxyaddr`, `proxyport`, `useproxypass`, `proxyuser`, `proxypass` (most can be empty strings/arrays).
6. **Export `type` is `confinline`**, not `inline` — the API has specific type codes like `confzip`, `confinline`, `confinlinedroid`, etc.

**Test added:** `test_action_vpn_openvpn_client_export` — custom test covering both `client_export` (POST action) and `client_export/config` (CRUD skip via custom coverage). Full cleanup in nested try/finally blocks.

**Decision:** Unblocked. The `pfSense-pkg-openvpn-client-export` package was already pre-installed in the golden image.

---

## 6. DHCP server POST returns 400 by design

**Endpoint:** `POST /api/v2/services/dhcp_server`

**Root cause:** This is **by design**, not a bug. The DHCPServer model is a per-interface singleton (`many=false`, keyed by interface name like `lan`, `opt1`). DHCP server configurations are **automatically initialized** when an interface gets a static IP address. You cannot "create" a DHCP server entry because it already exists for every eligible interface. Release v2.6.5 explicitly fixed an issue (#781) where "DHCPServer model could unintentionally initialize a DHCP server configuration for non-static interfaces," confirming the auto-creation pattern.

**The correct approach is to mark POST as "not applicable" and test with PATCH instead:**

```bash
# Read the existing DHCP config for LAN
GET /api/v2/services/dhcp_server?id=lan

# Update it
PATCH /api/v2/services/dhcp_server
{"id": "lan", "enable": true, "range_from": "192.168.1.100",
 "range_to": "192.168.1.200"}
```

If you need to test POST-like behavior, create a new interface (Category 4 above) with a static IP, then PATCH its auto-created DHCP server entry. The interface creation triggers DHCP server initialization.

**Confidence:** High. This is confirmed by the framework design (`many=false` singletons don't support POST/create), release notes, and multiple GitHub discussions (#520, #616).

### Sprint 2 Result: DONE (docs only)

Confirmed as by-design. Re-categorized the skip reason from "per-interface singleton, POST not supported" to "per-interface singleton — POST not supported by design, PATCH tested via singleton". The `services/dhcp_server/backend` singleton test already exercises the GET/PATCH lifecycle.

**Decision:** Stays skipped for CRUD, but the skip is now correctly categorized as "not applicable" rather than a limitation. No new tests needed.

---

## 7. ACME endpoints are testable with a Pebble container

**Endpoints:** `POST /api/v2/services/acme/account_key/register`, `POST /api/v2/services/acme/certificate/issue`, `POST /api/v2/services/acme/certificate/renew`

**Root cause:** These endpoints call the underlying `acme.sh` tool, which contacts a real ACME server. Without a CA to talk to, they fail.

**The pfSense ACME package explicitly supports custom ACME server URLs.** From the official Netgate documentation (docs.netgate.com), under Services -> ACME -> Settings -> Custom ACME Servers, you can define a custom server with three fields: Internal ID (e.g., `pebble-local`), Display Name (e.g., `Local Pebble`), and Server URL (e.g., `https://10.0.2.2:14000/dir`). This custom server then appears in the Account Key dropdown alongside Let's Encrypt and ZeroSSL.

**Setup steps using Pebble (Let's Encrypt's official test ACME server):**

1. **Run Pebble on the host machine** (accessible from QEMU VM via NAT gateway, typically `10.0.2.2`):
   ```bash
   docker run -d --name pebble \
     -p 14000:14000 -p 15000:15000 \
     -e PEBBLE_VA_NOSLEEP=1 \
     -e PEBBLE_VA_ALWAYS_VALID=1 \
     letsencrypt/pebble
   ```
   The `PEBBLE_VA_ALWAYS_VALID=1` flag makes Pebble accept all challenges without actual validation — perfect for testing.

2. **Import Pebble's root CA** into pfSense (via SSH or API):
   ```bash
   # Pebble's root CA is available at https://10.0.2.2:15000/roots/0
   curl -k https://10.0.2.2:15000/roots/0 >> /usr/local/share/certs/ca-root-nss.crt
   ```

3. **Configure the custom ACME server** via the API (if the `ACMESettings` model supports it) or via the pfSense GUI at Services -> ACME Certificates -> Settings.

4. **Create an account key** pointing to the Pebble server, then register it:
   ```bash
   POST /api/v2/services/acme/account_key
   {"name": "pebble-test", "acmeserver": "pebble-local", ...}

   POST /api/v2/services/acme/account_key/register
   {"id": "pebble-test"}
   ```

5. **Issue a certificate** using HTTP-01 standalone challenge (the ACME package supports standalone mode, binding to a temporary HTTP server on a configurable port).

An alternative to Pebble is the **Let's Encrypt staging environment** (`https://acme-staging-v02.api.letsencrypt.org/directory`), which is a built-in option in the pfSense ACME package dropdown — no custom server needed. However, staging still requires real DNS resolution and challenge validation, making Pebble with `PEBBLE_VA_ALWAYS_VALID=1` far simpler for test automation.

**Confidence:** High for the Pebble approach (the ACME package explicitly supports custom servers). The main risk is network connectivity between the QEMU VM and the host's Docker container.

### Sprint 7 Result

**DONE** — Pebble was NOT needed. All three ACME endpoints (register, issue, renew) are fully async and return 200 immediately with `status: pending`, regardless of whether acme.sh can actually reach the ACME server. The background process runs (and may fail), but the REST API endpoint itself works correctly.

Key findings:
- `acmeserver` field on account keys validates against a fixed enum: `letsencrypt-staging-2`, `letsencrypt-production-2`, `zerossl-production`, etc. Custom server names are rejected with `FIELD_INVALID_CHOICE`. Pebble would require bypassing REST API validation via PHP/config.xml.
- Using `letsencrypt-staging-2` works fine — the register/issue/renew endpoints fire-and-forget the acme.sh process and return 200 immediately.
- Single custom test `test_action_acme_register_issue_renew` covers all three endpoints in one test function: create account key, register, create cert, issue, renew, cleanup.
- 206 → 207 tests. No external infrastructure needed.

---

## 8. Settings sync needs an HA peer and should likely stay skipped

**Endpoint:** `POST /api/v2/system/restapi/settings/sync`

**Root cause:** This endpoint triggers XMLRPC synchronization of REST API settings to an HA peer over HTTPS/443. Without a configured sync target, it either times out waiting for a connection or fails on missing configuration. Issue #97 documents the HA sync feature request, with the developer confirming it was never automated — the manual workaround is `pfsense-api backup` / `pfsense-api restore` via SCP.

The REST API v2 Dispatcher framework may make the sync call asynchronous (returning 200 immediately, with the actual sync running in background). If so, calling the endpoint might "succeed" (return 200) even without a peer, with the failure only logged. This would allow testing the endpoint's HTTP response without actual sync.

**Potential workaround — configure sync to localhost:**

```bash
# Configure HA sync to point at the same machine
# Via pfSense GUI: System -> High Avail Sync -> Sync to 127.0.0.1
# With admin credentials
```

This would cause the box to sync REST API settings to itself. The XMLRPC call should succeed (the target is running pfSense with the REST API package), and the operation completes quickly. The risk is that this could cause unexpected configuration side effects, though syncing identical settings to the same box should be a no-op.

**If the endpoint uses a Dispatcher** (async), simply calling `POST /api/v2/system/restapi/settings/sync` might return 200 immediately regardless of HA configuration, with the actual sync failure only appearing in system logs.

**Confidence:** Low. Testing this properly requires either a second VM (expensive) or the localhost hack (risky). If the Dispatcher makes it async, confidence rises to Medium. **Recommendation: skip this endpoint** unless the test infrastructure can support a second pfSense VM.

---

## 9. REST API version endpoint triggers a package reinstall

**Endpoint:** `PATCH /api/v2/system/restapi/version`

**Root cause:** This endpoint **triggers an upgrade, downgrade, or reinstallation of the REST API package itself**. Per pfrest.org documentation: "You can update or revert the package to a specified version by sending a request to PATCH /api/v2/system/restapi/version. Set the `install_version` field to the desired version." Under the hood, it runs the equivalent of `pfsense-restapi revert <version>`, which downloads and installs the specified package version. Issue #691 shows this calls `get_all_available_versions()` -> `get_latest_api_version()` -> `get_api_version_details()` internally.

**This endpoint is genuinely destructive:**
- The API is unavailable during package reinstallation
- A version change can introduce breaking changes in the API schema
- Network issues during download can leave the API package broken
- It requires internet access to download the package from GitHub

**Potential "safe" test — PATCH to the same version:**

```bash
PATCH /api/v2/system/restapi/version
{"install_version": "v2.7.1"}
```

Re-installing the same version should be a no-op or at worst a brief reinstall cycle. However, this still triggers a `pkg` operation that may hit the 504 nginx timeout (same as Category 3), and the API becomes temporarily unavailable. **If tested, it must be the absolute last test in the suite**, after all other tests have completed, and ideally with a VM snapshot to roll back to.

A safer approach is to **only test GET** (read the current version) and skip PATCH entirely:

```bash
GET /api/v2/system/restapi/version
# Returns current version info without modification
```

**Confidence:** Low for safe testing. The reinstall is too risky for automated CI. **Recommendation: keep this skipped** in automated test suites. If manual testing is needed, snapshot the VM first and test as the very last operation.

---

## Consolidated scorecard and recommended test order

| # | Category | Endpoints | Verdict | Confidence | Unblocks |
|---|----------|-----------|---------|------------|----------|
| 4 | Interface CRUD | POST/PATCH/DELETE | **VLAN on em2** | High | 3 |
| 6 | DHCP server | POST | **Skip POST, already covered by PATCH** | High | 1 |
| 5 | OpenVPN export | POST + GET/DELETE config | **6-step setup chain** | High | 3 |
| 3 | Package install | POST/DELETE | **Pre-install + small-pkg test** | High | 2 |
| 7 | ACME endpoints | register/issue/renew | **Pebble container** | High | 3 |
| 2 | PKCS12 export | POST | **Accept: application/octet-stream** | Medium | 1 |
| 1 | HAProxy sub-resources | POST dns_resolver/email_mailer | **Init config.xml first** | Medium | 2 |
| 8 | Settings sync | POST | **Skip or localhost hack** | Low | 1 |
| 9 | REST API version | PATCH | **Keep skipped** | Low | 0 |

The recommended execution order prioritizes high-confidence, low-risk unblocks first. Categories 4, 6, 5, 3, and 7 together unblock **12 of 16 endpoints** with high confidence. Categories 1 and 2 add 3 more at medium confidence. Categories 8 and 9 (1 endpoint combined, since #6 should just be re-categorized as "not applicable") are best left skipped unless the infrastructure supports a second VM.

## What to do if the HAProxy workaround still fails

The user specifically noted they already tried PATCHing the parent settings without success. If the config.xml initialization approach from Category 1 also fails, the most likely explanation is a **framework-level bug** in how the Model base class resolves singleton parent models for nested child creation. The `__construct` method in `Model.inc` (line ~373, per the memory exhaustion errors in discussion #520) handles parent model resolution, and the singleton path may have an edge case where `init_config()` isn't called before `get_config()`. **File a new GitHub issue** at github.com/pfrest/pfSense-pkg-RESTAPI with the exact error response, the request body, and the output of `cat /cf/conf/config.xml | grep -A5 haproxy` to confirm config state. Reference issues #764 and #781 as prior art for parent/child initialization bugs.
