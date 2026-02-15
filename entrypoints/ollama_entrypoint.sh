#!/bin/sh

set -e
ollama serve --host 0.0.0.0 &
while curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 1
done
ollama pull gemma3:4b
wait