#!/bin/bash

# Usage: ./invoke_agent.sh [alarming|discovery|investigator|reporting] "your prompt here"

AGENT="$1"
PROMPT="$2"

if [[ "$AGENT" == "" || "$PROMPT" == "" ]]; then
  echo "Usage: $0 [alarming|discovery|investigator|reporting] \"your prompt here\""
  exit 1
fi

case "$AGENT" in
  alarming|discovery|investigator|reporting)
    ;;
  *)
    echo "Unknown agent: $AGENT"
    exit 1
    ;;
esac

# Run agentcore invoke for the selected agent and pipe to format_output.py
(cd agents/"$AGENT" && agentcore invoke "{\"prompt\": \"$PROMPT\"}") | python3 format_output.py