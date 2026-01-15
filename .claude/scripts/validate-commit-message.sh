#!/bin/bash

# Check if the command is a git commit command
if echo "$CLAUDE_TOOL_INPUT" | grep -q "git commit"; then
  # Extract the commit message (assuming -m "message" format for now)
  # This is a simplification and might need to be more robust for other commit options
  commit_message=$(echo "$CLAUDE_TOOL_INPUT" | sed -n 's/.*git commit -m "\([^"]*\)".*/\1/p')

  # Validate commit message format: "TYPE: description"
  if [[ "$commit_message" =~ ^[A-Z_]+:\ .*$ ]]; then
    echo "Commit message format is valid."
    exit 0
  else
    echo "Error: Invalid commit message format. Expected 'TYPE: description'."
    echo "Commit message: '$commit_message'"
    exit 1
  fi
fi

# If not a git commit command, allow it to proceed
exit 0
