## Task 07: Certificate Management

**task_id**: 07-certificate-management

**Objective**: Generate a CA, generate a certificate signed by that CA, then clean up.

**Steps**:
1. Generate a new Certificate Authority:
   - descriptive name: `bt_test_ca`
   - method: internal (generate, not import)
   - Key type/length: RSA 2048
   - Digest: SHA256
   - Lifetime: 3650
   - Common name: `bt_test_ca`
   - Distinguished name fields: country=US, state=CA, city=SanFrancisco, org=TestOrg, ou=TestUnit
   - **IMPORTANT**: All DN fields (country, state, city, org, OU) are required — omitting them causes a 500 error
2. Verify the CA was created by listing CAs or getting it by ID
3. Generate a certificate signed by this CA:
   - descriptive name: `bt_test_cert`
   - method: internal
   - CA reference: use the refid from step 1
   - Key type/length: RSA 2048
   - Digest: SHA256
   - Lifetime: 365
   - Common name: `bt_test_cert`
   - DN fields: same as above
4. Verify the certificate was created
5. Delete the certificate first
6. Delete the CA

**Expected outcome**: CA created, cert signed by CA created. Cert deleted before CA (dependency order).

**Cleanup**: Delete cert (step 5), then CA (step 6).
