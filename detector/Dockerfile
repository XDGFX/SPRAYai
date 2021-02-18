FROM nvcr.io/nvidia/l4t-base:r32.5.0

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y wget git ca-certificates build-essential python3-pip software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get install -y python3.9 python3.9-distutils
RUN pip3 install --upgrade pip

# Start Darknet Install
RUN git clone --depth 1 https://github.com/AlexeyAB/darknet /var/local/darknet

WORKDIR /var/local/darknet

# Copy Makefile for darknet
COPY Makefile Makefile

# Redirect environment variables to correct locations
ENV CPATH=/usr/local/cuda/targets/aarch64-linux/include:$CPATH
ENV LD_LIBRARY_PATH=/usr/local/cuda/targets/aarch64-linux/lib:$LD_LIBRARY_PATH
ENV PATH=/usr/local/cuda/bin:$PATH

# Compile darknet
RUN make

# Setup Python
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 2
RUN pip3 install numpy pillow yolo-v4 flask

# Copy custom files
COPY . .
# COPY test test
# COPY real real
# COPY yolov4-tiny.weights yolov4-tiny.weights
# COPY yolov4-tiny.cfg yolov4-tiny.cfg

# Run with
# ./darknet detect yolov4-tiny.cfg yolov4-tiny.weights test/1003.jpg