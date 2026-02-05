#!/bin/bash

set -e
ollama serve &
sleep 5
ollama pull gemma3:4b
wait