# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim

EXPOSE 5002

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# My app specific environment vars
ENV DATE=$DATE
ENV TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID} 
ENV TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN} 
ENV REDIS_HOST=${REDIS_HOST} 
ENV REDIS_PORT=${REDIS_PORT} 
ENV REDIS_PW=${REDIS_PW} 
ENV SUDOKU_SOLVER_URL=${SUDOKU_SOLVER_URL} 
ENV WT_SECRET=${JWT_SECRET}

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

RUN ls -l

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "sudoku-bot:app"]
