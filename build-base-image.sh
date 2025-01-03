#!/bin/bash
echo "Be sure to start docker.app first"

docker rmi kineticsquid/sudoku-bot-base:latest
docker build -t kineticsquid/sudoku-bot-base:latest -f Dockerfile-base .
docker push kineticsquid/sudoku-bot-base:latest

# list the current images
echo "Files..."
ls -R

# list the current images
echo "Docker Images..."
docker images