#!/usr/bin/env bash

# Create a temporary directory for the home directory
export HOME=$(mktemp -d)

echo "[+] Key Setup Started ..."

mkdir $HOME/.ssh
cp /home/abdul/artiq_fork/ssh_keys/id_ed25519 $HOME/.ssh/id_ed25519
cp /home/abdul/.ssh/id_ed25519.pub $HOME/.ssh/id_ed25519.pub
echo "rpi-1 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIACtBFDVBYoAE4fpJCTANZSE0bcVpTR3uvfNvb80C4i5" > $HOME/.ssh/known_hosts
chmod 600 $HOME/.ssh/id_ed25519

echo "[+] Key Setup Completed"

# Create a temporary directory for the lock control
LOCKCTL=$(mktemp -d)
mkfifo $LOCKCTL/lockctl

echo "[+] Waiting for lock"

# Acquire a lock on the remote 'rpi-1' host
cat $LOCKCTL/lockctl | ssh -i $HOME/.ssh/id_ed25519 -o UserKnownHostsFile=$HOME/.ssh/known_hosts rpi-1 'mkdir -p /tmp/board_lock && flock /tmp/board_lock/kc705-1 -c "echo Ok; cat"' | (

    # Set up a trap to release the lock when the script exits
    atexit_unlock() {
    echo > $LOCKCTL/lockctl
    }
    trap atexit_unlock EXIT

    # Read the "Ok" line from the remote lock acquisition
    read LOCK_OK
    echo "[+] Lock Acquired ..."
    # Flash the ARTIQ firmware to the 'kc705' target on the 'rpi-1' host
    artiq_flash --srcbuild -t kc705 -H rpi-1 -d /home/abdul/artiq_fork/artiq_kc705/nist_clock

    echo "[+] Entering Sleep"
    sleep 30
    echo "[+] Resuming Execution"
    export ARTIQ_ROOT="/home/abdul/artiq_fork/artiq/examples/kc705_nist_clock"
    export ARTIQ_LOW_LATENCY=1

    # Run the ARTIQ tests for the 'coredevice'

    python -m unittest -v artiq.test.coredevice.test_exceptions.ExceptionTest.test_exceptions
    echo "[+] Test Completed"
)
