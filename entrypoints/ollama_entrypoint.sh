#!/bin/sh

set -e
ollama serve &
until curl -sf http://localhost:11434/api/tags > /dev/null; do
    sleep 1
done
ollama pull gemma3:4b
ollama pull gemma3:12b
ollama pull gemma4:e4b
wait
