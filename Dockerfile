# For more information, please refer to https://aka.ms/vscode-docker-python
# FROM python:3.8-windowsservercore
FROM python:3.8

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt
RUN [ "python", "-c", "import nltk; nltk.download('punkt')" ]
RUN [ "python", "-c", "import nltk; nltk.download('averaged_perceptron_tagger')" ]
RUN [ "python", "-c", "import nltk; nltk.download('maxent_ne_chunker')" ]
RUN [ "python", "-c", "import nltk; nltk.download('words')" ]
RUN [ "python", "-m", "spacy", "download", "en_core_web_sm" ]
# ADD nltk_data C:\\nltk_data
WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
# RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
# USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "app.py"]
