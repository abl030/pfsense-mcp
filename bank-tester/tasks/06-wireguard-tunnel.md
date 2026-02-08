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
   - allowed IPs: `10.99.0.2/32`
   - The peer needs to reference the tunnel (by ID or tun_* name)
5. Apply WireGuard changes
6. List peers and verify the new peer appears
7. Delete the peer
8. Apply WireGuard changes
9. Delete the tunnel
10. Apply WireGuard changes

**Expected outcome**: Tunnel and peer created. Peer references parent tunnel. Cleanup in reverse order (peer before tunnel).

**Cleanup**: Delete peer (step 7), then tunnel (step 9). Apply after each delete.
