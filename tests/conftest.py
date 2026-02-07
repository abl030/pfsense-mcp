"""
Pytest fixtures for pfSense VM integration tests.

Provides an isolated QEMU VM per test session:
  1. Copies vm/golden.qcow2 → temp file
  2. Boots QEMU with port-forwarded HTTPS + SSH
  3. Waits for the REST API to become ready
  4. Yields an httpx client configured for the API
  5. Kills QEMU and deletes the temp image
"""

import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_IMAGE = REPO_ROOT / "vm" / "golden.qcow2"
API_KEY_FILE = REPO_ROOT / "vm" / "api-key.txt"

HTTPS_PORT = 18443  # Use high port to avoid conflicts with setup.sh
SSH_PORT = 12222

API_READY_TIMEOUT = 120  # seconds
API_POLL_INTERVAL = 2  # seconds


def _find_free_port(start: int) -> int:
    """Find a free port starting from `start`."""
    import socket

    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free port found in range {start}-{start + 100}")


class PfSenseVM:
    """Manages a QEMU pfSense VM instance for testing."""

    def __init__(self, qcow2_path: Path, https_port: int, ssh_port: int):
        self.qcow2_path = qcow2_path
        self.https_port = https_port
        self.ssh_port = ssh_port
        self.process: subprocess.Popen | None = None
        self.base_url = f"https://127.0.0.1:{https_port}"

    def start(self) -> None:
        """Boot the VM in background."""
        self.process = subprocess.Popen(
            [
                "qemu-system-x86_64",
                "-m", "1024",
                "-enable-kvm",
                "-drive", f"file={self.qcow2_path},if=virtio,format=qcow2",
                "-nographic",
                "-net", "nic,model=virtio",
                "-net", f"user,hostfwd=tcp::{self.https_port}-:443,hostfwd=tcp::{self.ssh_port}-:22",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )

    def wait_for_api(self, timeout: int = API_READY_TIMEOUT) -> None:
        """Poll the API until it responds with 200."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                resp = httpx.get(
                    f"{self.base_url}/api/v2/system/version",
                    auth=("admin", "pfsense"),
                    verify=False,
                    timeout=5,
                )
                if resp.status_code == 200:
                    return
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout):
                pass
            time.sleep(API_POLL_INTERVAL)
        raise TimeoutError(f"pfSense API not ready after {timeout}s")

    def stop(self) -> None:
        """Kill the VM."""
        if self.process and self.process.poll() is None:
            self.process.send_signal(signal.SIGTERM)
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


@pytest.fixture(scope="session")
def pfsense_vm(tmp_path_factory):
    """
    Session-scoped fixture: boots a pfSense VM from the golden image.

    Yields a PfSenseVM instance with the API ready.
    """
    if not GOLDEN_IMAGE.exists():
        pytest.skip(f"Golden image not found: {GOLDEN_IMAGE}. Run vm/setup.sh first.")

    # Copy golden image to temp location
    tmp_dir = tmp_path_factory.mktemp("pfsense")
    test_image = tmp_dir / "pfsense-test.qcow2"
    shutil.copy2(GOLDEN_IMAGE, test_image)

    # Find free ports
    https_port = _find_free_port(HTTPS_PORT)
    ssh_port = _find_free_port(SSH_PORT)

    vm = PfSenseVM(test_image, https_port, ssh_port)
    vm.start()

    try:
        vm.wait_for_api()
    except TimeoutError:
        vm.stop()
        raise

    yield vm

    vm.stop()


@pytest.fixture(scope="session")
def api_client(pfsense_vm: PfSenseVM) -> httpx.Client:
    """
    Session-scoped httpx client authenticated against the test VM.

    Uses BasicAuth (admin:pfsense) by default. If an API key exists,
    uses X-API-Key header instead.
    """
    api_key = None
    if API_KEY_FILE.exists():
        api_key = API_KEY_FILE.read_text().strip()

    if api_key:
        client = httpx.Client(
            base_url=pfsense_vm.base_url,
            headers={"X-API-Key": api_key},
            verify=False,
            timeout=30,
        )
    else:
        client = httpx.Client(
            base_url=pfsense_vm.base_url,
            auth=("admin", "pfsense"),
            verify=False,
            timeout=30,
        )

    yield client
    client.close()


@pytest.fixture(scope="session")
def basic_auth_client(pfsense_vm: PfSenseVM) -> httpx.Client:
    """Session-scoped httpx client using BasicAuth (always works)."""
    client = httpx.Client(
        base_url=pfsense_vm.base_url,
        auth=("admin", "pfsense"),
        verify=False,
        timeout=30,
    )
    yield client
    client.close()
