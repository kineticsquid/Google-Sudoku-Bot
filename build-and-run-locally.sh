#!/bin/bash
echo "Be sure to start docker.app first"

docker rmi kineticsquid/google-sudoku-bot:latest
docker build -t kineticsquid/google-sudoku-bot:latest .
# docker push kineticsquid/google-sudoku-bot:latest

# list the current images
echo "Docker Images..."
docker images

echo "Now running..."
./.vscode/run-image-locally.sh