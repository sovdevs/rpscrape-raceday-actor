FROM apify/actor-python:3.11

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Clone and setup rpscrape
RUN git clone https://github.com/joenano/rpscrape.git && \
    cd rpscrape && \
    pip install --no-cache-dir -r requirements.txt

# Copy actor code
COPY . ./

# Run the actor
CMD ["python", "-m", "src"]