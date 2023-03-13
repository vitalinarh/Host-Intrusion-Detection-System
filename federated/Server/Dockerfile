FROM python:3.7.3-stretch

RUN mkdir /app
WORKDIR /app
COPY Datasets /Datasets
COPY . .

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# Put files at the image '/server/' folder.
ADD server.py /app/
# '/server/' is base directory
WORKDIR /app/
# Expose port 9898 in the container
EXPOSE 9898
# execute the command
CMD [ "python3", "/app/server.py" ]