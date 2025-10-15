## Project Todo & Docker Integration Plan

### High-Level Architecture (All x86_64)

```
Host (macOS ARM64)
  └─ Docker (x86_64 emulation via Rosetta)
       ├─ ringshell (x86_64)
       │   ├─ LangGraph / Agent
       │   └─ HTTP client tools → CTP service
       └─ ctp-service (x86_64)
           ├─ FastAPI wrapper
           └─ CTP libs: libthostmduserapi.so, libthosttraderapi.so
```

### Environments
- Development: Same x86_64 containers as production (emulated on M3).
- Production: x86_64 containers running natively on cloud servers.

### Compose Overview
- Service `ringshell`: main agent application.
- Service `ctp-service`: FastAPI wrapper over CTP API and shared objects.

---

## TODO List

- [ ] Add Docker integration plan and TODO list to README.md
- [ ] Create CTP library structure under `ctp/lib` with copy instructions
- [ ] Add CTP service requirements file `ctp/requirements.txt`
- [ ] Create CTP service Dockerfile for x86_64 at `ctp/Dockerfile`
- [ ] Implement FastAPI CTP wrapper at `ctp/src/service.py` (stubs allowed)
- [ ] Implement LangGraph HTTP tools client at `ctp/src/client.py` (stubs)
- [ ] Create `ctp/src/__init__.py` and placeholders
- [ ] Update root `requirements.txt` to include `httpx`
- [ ] Update root `Dockerfile` to enforce x86_64 and keep current setup
- [ ] Update `docker-compose.yml` to include `ctp-service`
- [ ] Create `.env.example` with credential variables
- [ ] Verify build: `docker-compose up --build`
- [ ] Add basic connectivity tests

---

## Setup Steps

### 1) Copy CTP Libraries

Copy the following files from `~/Downloads/v6.3.15/linux64/` into `ctp/lib/`:

```
libthostmduserapi.so
libthosttraderapi.so
error.xml
error.dtd
```

Commands:
```
mkdir -p ctp/lib
cp ~/Downloads/v6.3.15/linux64/*.so ctp/lib/
cp ~/Downloads/v6.3.15/linux64/*.xml ctp/lib/
cp ~/Downloads/v6.3.15/linux64/*.dtd ctp/lib/
```

### 2) Environment Variables (.env)

```
CTP_BROKER_ID=BHCT001
CTP_USER_ID=20600
CTP_PASSWORD=REDACTED
CTP_MD_SERVER=tcp://222.73.120.220:31213
CTP_TRADE_SERVER=tcp://222.73.120.220:31205
# CTP_APP_ID=YOUR_APP_ID   # required for v6.3.15 auth
# CTP_AUTH_CODE=YOUR_AUTH  # required for v6.3.15 auth
```

---

## Run

```
docker-compose up --build
```


