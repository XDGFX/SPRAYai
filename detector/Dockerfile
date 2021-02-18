FROM nvcr.io/nvidia/l4t-base:r32.5.0

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y wget git ca-certificates build-essential software-properties-common vim

# # Start Darknet Install
# RUN git clone --depth 1 https://github.com/AlexeyAB/darknet /var/local/darknet

# WORKDIR /var/local/darknet

# # Copy Makefile for darknet
# COPY Makefile Makefile

# # Redirect environment variables to correct locations
# ENV CPATH=/usr/local/cuda/targets/aarch64-linux/include:$CPATH
# ENV LD_LIBRARY_PATH=/usr/local/cuda/targets/aarch64-linux/lib:$LD_LIBRARY_PATH
# ENV PATH=/usr/local/cuda/bin:$PATH

# # Compile darknet
# RUN make

# Setup Python
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get install -y python3.9 python3.9-distutils
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 2

RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3 get-pip.py --force-reinstall

RUN pip3 install numpy pillow opencv-python flask

# # Fix for scikit-image failure
# RUN apt-get install -y libaec-dev libblosc-dev libffi-dev libbrotli-dev libboost-all-dev libbz2-dev 
# RUN apt-get install -y libgif-dev libopenjp2-7-dev liblcms2-dev libjpeg-dev libjxr-dev liblz4-dev liblzma-dev libpng-dev libsnappy-dev libwebp-dev libzopfli-dev libzstd-dev
# # RUN wget https://github.com/scipy/scipy/releases/download/v1.3.3/scipy-1.3.3.tar.gz && tar -xzvf scipy-1.3.3.tar.gz scipy-1.3.3 && cd scipy-1.3.3/ && python3 setup.py install --user
# RUN wget https://download.osgeo.org/libtiff/tiff-4.1.0.tar.gz && tar -xzvf tiff-4.1.0.tar.gz
# RUN cd tiff-4.1.0/ && ./configure
# RUN make
# RUN make install
# RUN apt-get install -y python3-sklearn

# RUN pip3 install imagecodecs
# RUN pip3 install scikit-image

# RUN pip3 install yolo-v4 flask

COPY app /app
WORKDIR /app

# Get model
RUN wget -O "yolov4-tiny.cfg" "https://github.com/XDGFX/navvy-spray-ai/releases/download/4.0/custom-yolov4-tiny-detector.cfg"
RUN wget -O "yolov4-tiny.weights" "https://github.com/XDGFX/navvy-spray-ai/releases/download/4.0/custom-yolov4-tiny-detector_best_4000.weights"

EXPOSE 5050

#Run the command
CMD python3 app.py