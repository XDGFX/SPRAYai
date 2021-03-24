# vision Dockerfile

# Builds a vision container for the SPRAYai system.

# Callum Morrison, 2021

FROM python:3.9

# Install requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Copy program files
COPY *.py /app
WORKDIR /app

CMD ["python", "/host.py"]