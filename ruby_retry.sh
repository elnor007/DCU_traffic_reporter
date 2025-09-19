#!/bin/bash
# Usage: ./retry.sh <working_dir> <command> [max_retries] [delay_seconds]

echo -e "\n\n\n\n\n$(date -u +%Y-%m-%d-%H-%M-%S-%H-%M-%S) : $(basename "$0") has been initiated.\n"

working_dir="$1"    # Directory to cd into (e.g., "/home/ec2-user/vivacity/ruby")
command="$2"        # Command to run (e.g., the Ruby reporter command)
max_retries1="${3:-3}"  # Default: 3 retries
delay1="${4:-2}"       # Default: 2-second delay
attempt1=0

# Checking if email script is watching reports directory
attempt2=0
max_retries2=10
delay2=1


# Change directory
cd "$working_dir" || { echo -e "$(date +%Y-%m-%d-%H-%M-%S) : Failed to cd to $working_dir\n"; exit 1; }

while [[ $attempt1 -lt $max_retries1 ]]; do
  echo -e "$(date -u +%Y-%m-%d-%H-%M-%S) : Attempt $((attempt1 + 1)) of $max_retries1...\n"
  attempt2=0  
  
  # Run the command and capture exit code
  while [[ $attempt2 -lt $max_retries2 ]]; do
    if [ -f "/tmp/email_watcher.lock" ]; then
      eval "$command"
      exit_code=$?
      break
    else
      echo -e "$(date +%Y-%m-%d-%H-%M-%S) : Email script PDF observer is offline, retrying...\n"
      ((attempt2++))
      sleep "$delay2"
      continue
    fi
  done 

  if [[ $attempt2 -eq $max_retries2 ]]; then
      echo -e "$(date +%Y-%m-%d-%H-%M-%S) : Email script PDF observer is still offline, aborting script...\n"
      exit 2
  fi

  if [[ $exit_code -eq 0 ]]; then
    echo -e "Success!"
    exit 0
  fi

  ((attempt1++))
  echo -e "$(date +%Y-%m-%d-%H-%M-%S) : Failed (exit code: $exit_code). Retrying in $delay1 seconds...\n"
  sleep "$delay1"

done

echo -e "$(date +%Y-%m-%d-%H-%M-%S) : Max retries reached. Aborting...\n\n\n\n\n" >&2
exit 2
