FROM ubuntu:16.04 as build

# Installing conda for python package management
# Install base utilities
RUN apt-get update && \
    apt-get install -y wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# Install miniconda
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
     /bin/bash ~/miniconda.sh -b -p /opt/conda
# Put conda in path so we can use conda activate
ENV PATH=$CONDA_DIR/bin:$PATH

# Installing conda-pack to reduce conda docker image size
RUN conda update python -y && \
    conda install -y conda-pack && \
    conda clean -a

RUN mkdir -p /home/code
COPY environment.yml environment-dev.yml /home/code/

# Creating conda environments venv and venv-dev
RUN conda env create -n apps -f /home/code/environment.yml && \
    conda-pack -n apps -o /tmp/env.tar && \
    mkdir /venv && cd /venv && tar xf /tmp/env.tar && \
    /venv/bin/conda-unpack && \
    rm /tmp/env.tar && \
    conda env update -n apps -f /home/code/environment-dev.yml && \
    conda-pack -n apps -o /tmp/env.tar && \
    mkdir /venv-dev && cd /venv-dev && tar -xf /tmp/env.tar && \
    /venv-dev/bin/conda-unpack && \
    rm /tmp/env.tar && \
    conda env remove -n apps && \
    conda clean -a
    
FROM alpine:latest as dev
COPY --from=build /venv-dev/ /venv-dev/
ENV PATH="/venv-dev/bin:${PATH}"

FROM alpine:latest as runtime
COPY --from=build /venv/ /venv/
COPY . /work/
ENV PATH="/venv/bin:${PATH}"
WORKDIR /work
ENTRYPOINT [ "python", "/work/link/aggregator/main.py" ]
