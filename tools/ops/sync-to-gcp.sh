#!/bin/bash
# Sync bot code + research files from your Mac TO the GCP VM.
#
# Run on your Mac (from the repo root):   bash tools/ops/sync-to-gcp.sh
# Do NOT run this on the VM.
#
# What it does:
#   1. Starts the VM if it's stopped
#   2. Waits for SSH to be ready
#   3. Creates the directory tree on the VM (safe on fresh VMs)
#   4. Copies tools, config, research, and outreach files
#   5. Installs Python deps and restarts the bot service

set -e

PROJECT="gtm-agent-492216"
ZONE="us-central1-a"
INSTANCE="gtm-bot"
REMOTE="~/gtm-agent"

GCLOUD_FLAGS=(--project="$PROJECT" --zone="$ZONE")

# --- helpers ----------------------------------------------------------------

wait_for_ssh() {
  local i
  echo "  Waiting for SSH..."
  for i in $(seq 1 60); do
    if gcloud compute ssh "$INSTANCE" "${GCLOUD_FLAGS[@]}" --quiet --command="true" 2>/dev/null; then
      echo "  SSH ready."
      return 0
    fi
    sleep 3
  done
  echo "ERROR: SSH never became available after 3 minutes."
  echo "Try:  gcloud compute ssh $INSTANCE --project=$PROJECT --zone=$ZONE"
  exit 1
}

ensure_vm_running() {
  local status
  status=$(gcloud compute instances describe "$INSTANCE" "${GCLOUD_FLAGS[@]}" \
           --format='get(status)' 2>/dev/null) || {
    echo "ERROR: Instance '$INSTANCE' not found in project $PROJECT zone $ZONE."
    exit 1
  }

  if [[ "$status" != "RUNNING" ]]; then
    echo "  VM status: $status — starting..."
    gcloud compute instances start "$INSTANCE" "${GCLOUD_FLAGS[@]}" --quiet
  fi

  wait_for_ssh
}

remote_cmd() {
  gcloud compute ssh "$INSTANCE" "${GCLOUD_FLAGS[@]}" --quiet --command="$1"
}

# --- main -------------------------------------------------------------------

echo "=== Syncing to $INSTANCE ($ZONE) ==="
ensure_vm_running

echo "  Creating remote directories..."
remote_cmd "mkdir -p $REMOTE/tools $REMOTE/state $REMOTE/output/pipeline $REMOTE/output/research/icp-a-suite $REMOTE/output/research/icp-b-feed $REMOTE/output/research/icp-c-marketplace $REMOTE/output/research/icp-d-telecom $REMOTE/output/outreach/icp-a-suite $REMOTE/output/outreach/icp-b-feed $REMOTE/output/outreach/icp-c-marketplace $REMOTE/output/outreach/icp-d-telecom"

echo "  -> tools/"
gcloud compute scp "${GCLOUD_FLAGS[@]}" \
  tools/telegram/telegram-bot.py \
  tools/email/send-email.py \
  tools/apollo/apollo-enrich.py \
  tools/hubspot/hubspot-leads.py \
  tools/sheets/generate-weekly-tab.py \
  tools/telegram/vm-restart-bot.sh \
  tools/email/email-config.json \
  tools/hubspot/hubspot-config.json \
  "$INSTANCE:$REMOTE/tools/"

echo "  -> state/ (hubspot-mapping.json — required by bot's HubSpot write commands)"
gcloud compute scp "${GCLOUD_FLAGS[@]}" \
  state/hubspot-mapping.json \
  "$INSTANCE:$REMOTE/state/"

echo "  -> requirements.txt"
gcloud compute scp "${GCLOUD_FLAGS[@]}" requirements.txt "$INSTANCE:$REMOTE/"

echo "  -> output/research/"
for d in output/research/icp-*/; do
  [ -d "$d" ] || continue
  gcloud compute scp "${GCLOUD_FLAGS[@]}" --recurse "$d" "$INSTANCE:$REMOTE/output/research/"
done

echo "  -> output/outreach/"
for d in output/outreach/icp-*/; do
  [ -d "$d" ] || continue
  gcloud compute scp "${GCLOUD_FLAGS[@]}" --recurse "$d" "$INSTANCE:$REMOTE/output/outreach/"
done

echo "  Installing deps & restarting bot..."
remote_cmd "cd $REMOTE && pip3 install --break-system-packages -q -r requirements.txt 2>/dev/null; sudo systemctl restart gtm-bot 2>/dev/null || echo 'NOTE: gtm-bot systemd service not set up yet — run tools/vm-restart-bot.sh on the VM to start manually (note: on the VM, the bot files are flat under ~/gtm-agent/tools/, so the local subfolder structure does not propagate)'"

echo "=== Sync complete ==="
