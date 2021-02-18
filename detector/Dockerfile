# detector Dockerfile

# Builds a Flask-based object detection API webserver,
# using weights from a custom trained YOLOv4 darknet model.

# Callum Morrison, 2021

FROM nvcr.io/nvidia/l4t-base:r32.5.0

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y wget git ca-certificates build-essential software-properties-common vim

# Setup Python
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get install -y python3.9 python3.9-distutils
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 2

# Install pip
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3 get-pip.py --force-reinstall

# Install dependencies
RUN pip3 install numpy pillow opencv-python flask

# Copy webserver files
COPY app /app
WORKDIR /app

# Get model
RUN wget -O "yolov4-tiny.cfg" "https://github.com/XDGFX/navvy-spray-ai/releases/download/4.0/custom-yolov4-tiny-detector.cfg"
RUN wget -O "yolov4-tiny.weights" "https://github.com/XDGFX/navvy-spray-ai/releases/download/4.0/custom-yolov4-tiny-detector_best_4000.weights"

EXPOSE 5050

# Start the webserver
CMD python3 app.py