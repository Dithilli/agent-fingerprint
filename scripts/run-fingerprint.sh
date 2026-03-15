#!/bin/bash
# Agent Fingerprint — Run the questionnaire and save a baseline
#
# Usage: ./run-fingerprint.sh [output-dir]
# Output dir defaults to ./fingerprints/
#
# This script is meant to be invoked by the agent via exec.
# The agent reads questions.md, answers each question, and saves
# the results as a timestamped JSON file.
#
# Since the agent itself needs to answer the questions, this script
# just sets up the output directory and prints instructions.

OUTPUT_DIR="${1:-./fingerprints}"
mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
MODEL=${2:-"unknown"}
AGENT=${3:-"unknown"}

# Sanitize model name for filename
MODEL_SAFE=$(echo "$MODEL" | tr '/' '-' | tr ':' '-')

OUTFILE="$OUTPUT_DIR/${AGENT}_${MODEL_SAFE}_${TIMESTAMP}.json"

echo "FINGERPRINT_OUTPUT=$OUTFILE"
echo "FINGERPRINT_MODEL=$MODEL"
echo "FINGERPRINT_AGENT=$AGENT"
echo "FINGERPRINT_TIMESTAMP=$TIMESTAMP"
echo ""
echo "Ready. Agent should now answer all questions from references/questions.md"
echo "and write results as JSON to: $OUTFILE"
