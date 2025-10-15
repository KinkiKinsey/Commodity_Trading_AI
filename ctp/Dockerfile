FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# System deps (libstdc++)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libstdc++6 \
    build-essential \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy CTP shared libraries (mounted or copied into image)
COPY lib/ /usr/local/lib/ctp/
COPY include/ /usr/local/include/ctp/
ENV LD_LIBRARY_PATH=/usr/local/lib/ctp:$LD_LIBRARY_PATH

# Copy service code
COPY src/ /app/src/

# build native MD runner
RUN g++ -std=gnu++17 -O2 -I/usr/local/include/ctp \
    /app/src/md_runner.cpp -L/usr/local/lib/ctp \
    -lthostmduserapi -o /usr/local/bin/md_runner

# build login tester
RUN g++ -std=gnu++17 -O2 -I/usr/local/include/ctp \
    /app/src/md_login.cpp -L/usr/local/lib/ctp \
    -lthostmduserapi -o /usr/local/bin/md_login

# build trader instrument query tool
RUN g++ -std=gnu++17 -O2 -I/usr/local/include/ctp \
    /app/src/td_query_instruments.cpp -L/usr/local/lib/ctp \
    -lthosttraderapi -o /usr/local/bin/td_query_instruments

# build market data daemon (long-running process)
RUN g++ -std=gnu++17 -O2 -I/usr/local/include/ctp \
    /app/src/md_daemon.cpp -L/usr/local/lib/ctp \
    -lthostmduserapi -pthread -o /usr/local/bin/md_daemon

ENV PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["uvicorn", "src.service:app", "--host", "0.0.0.0", "--port", "8080"]


