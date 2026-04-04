#!/bin/bash
# Sync bot code + research files from your Mac TO the GCP VM.
#
# Run on your Mac (from the repo root):   bash tools/sync-to-gcp.sh
# Do NOT run this on the VM.
#
# What it does:
#   1. Starts the VM if it's stopped
#   2. Waits for SSH to be ready
#   3. Creates the directory tree on the VM (safe on fresh VMs)
#   4. Copies tools, config, research, and outreach files
#   5. Installs Python deps and restarts the bot service

set -e

ZONE="us-central1-a"
INSTANCE="gtm-bot"
REMOTE="~/gtm-agent"

# --- helpers ----------------------------------------------------------------

wait_for_ssh() {
  local i
  echo "  Waiting for SSH..."
  for i in $(seq 1 60); do
    if gcloud compute ssh "$INSTANCE" --zone="$ZONE" --quiet --command="true" 2>/dev/null; then
      echo "  SSH ready."
      return 0
    fi
    sleep 3
  done
  echo "ERROR: SSH never became available after 3 minutes."
  echo "Try:  gcloud compute ssh $INSTANCE --zone=$ZONE"
  exit 1
}

ensure_vm_running() {
  local status
  status=$(gcloud compute instances describe "$INSTANCE" --zone="$ZONE" \
           --format='get(status)' 2>/dev/null) || {
    echo "ERROR: Instance '$INSTANCE' not found in zone $ZONE."
    exit 1
  }

  if [[ "$status" != "RUNNING" ]]; then
    echo "  VM status: $status — starting..."
    gcloud compute instances start "$INSTANCE" --zone="$ZONE" --quiet
  fi

  wait_for_ssh
}

remote_cmd() {
  gcloud compute ssh "$INSTANCE" --zone="$ZONE" --quiet --command="$1"
}

# --- main -------------------------------------------------------------------

echo "=== Syncing to $INSTANCE ($ZONE) ==="
ensure_vm_running

echo "  Creating remote directories..."
remote_cmd "mkdir -p $REMOTE/tools $REMOTE/output/research/icp-a-suite $REMOTE/output/research/icp-b-feed $REMOTE/output/research/icp-c-marketplace $REMOTE/output/research/icp-d-telecom $REMOTE/output/outreach/icp-a-suite $REMOTE/output/outreach/icp-b-feed $REMOTE/output/outreach/icp-c-marketplace $REMOTE/output/outreach/icp-d-telecom"

echo "  -> tools/"
gcloud compute scp --zone="$ZONE" \
  tools/telegram-bot.py \
  tools/send-email.py \
  tools/apollo-enrich.py \
  tools/vm-restart-bot.sh \
  tools/email-config.json \
  "$INSTANCE:$REMOTE/tools/"

echo "  -> requirements.txt"
gcloud compute scp --zone="$ZONE" requirements.txt "$INSTANCE:$REMOTE/"

echo "  -> output/research/"
for d in output/research/icp-*/; do
  [ -d "$d" ] || continue
  gcloud compute scp --zone="$ZONE" --recurse "$d" "$INSTANCE:$REMOTE/output/research/"
done

echo "  -> output/outreach/"
for d in output/outreach/icp-*/; do
  [ -d "$d" ] || continue
  gcloud compute scp --zone="$ZONE" --recurse "$d" "$INSTANCE:$REMOTE/output/outreach/"
done

echo "  Installing deps & restarting bot..."
remote_cmd "cd $REMOTE && pip3 install -q -r requirements.txt 2>/dev/null; sudo systemctl restart gtm-bot 2>/dev/null || echo 'NOTE: gtm-bot systemd service not set up yet — run tools/vm-restart-bot.sh on the VM to start manually'"

echo "=== Sync complete ==="
