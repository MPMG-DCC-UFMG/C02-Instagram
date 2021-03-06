# Download base image ubuntu 16.04
FROM ubuntu:16.04

# Set encoding
ENV LANG C.UTF-8

# Update Ubuntu Software repository
RUN apt-get update -y && apt-get upgrade -y

# Install essential packages
RUN apt-get install -y wget curl zip

# Install python-related packages
RUN apt-get install -y python3

# Install kafka-needed java library
RUN apt-get install -y default-jre

# Install pip3
COPY get-pip.py /
RUN python3 /get-pip.py && rm /get-pip.py

# Install pip libraries
COPY requirements.txt /
RUN pip3 install --no-cache-dir -r requirements.txt

# Check freeze
# RUN pip3 freeze

# Create needed folders
RUN mkdir /home/mp && mkdir /home/mp/coletor-instagram

# Copy files to specified folders
COPY . /home/mp/coletor-instagram/

# Assure it worked
RUN pip3 freeze && find /home/mp/ -iname "*py"