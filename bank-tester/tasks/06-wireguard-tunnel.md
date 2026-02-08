## Task 06: WireGuard Tunnel

**task_id**: 06-wireguard-tunnel

**Objective**: Create a WireGuard tunnel with a peer, then clean up.

**Steps**:
1. Create a WireGuard tunnel:
   - description: `bt_wg_tunnel`
   - Listen port: 51820
   - Let the server generate keys (or provide them if required)
   - Address/network: `10.99.0.1/24`
2. Apply WireGuard changes
3. Get the tunnel to verify it was created and note its ID
4. Create a WireGuard peer on this tunnel:
   - description: `bt_wg_peer`
   - public key: `dGVzdHB1YmxpY2tleWZvcnBmc2Vuc2UxMjM0NTY3OA==` (dummy base64, 32 bytes)
   - The peer needs to reference the tunnel (by ID or tun_* name)
   - Do NOT pass `allowedips` inline — it is a sub-resource, not an inline parameter
5. Add an allowed IP to the peer using `pfsense_create_vpn_wire_guard_peer_allowed_ip`:
   - `address`: `10.99.0.2`
   - `mask`: `32`
   - `descr`: `bt_wg_allowedip`
   - `parent_id`: (use the peer ID from step 4)
6. Apply WireGuard changes
7. List peers and verify the new peer appears
8. Delete the allowed IP (before deleting the peer)
9. Delete the peer
10. Apply WireGuard changes
11. Delete the tunnel
12. Apply WireGuard changes

**Expected outcome**: Tunnel and peer created. Peer references parent tunnel. Cleanup in reverse order (peer before tunnel).

**Cleanup**: Delete allowed IP (step 8), then peer (step 9), then tunnel (step 11). Apply after each delete.
