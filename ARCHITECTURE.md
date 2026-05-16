## Docker
Note: As of May 16. 2026
There are only 4 docker images (= read-only, the blue print)
- Docker image (myfastapi:latest) > Docker containers (fastapi)
    - Inside the image there are a couple of abstract layers + EXPOSED ports + ENV vars + Metadata
    ```
    Layer 4: your app code (COPY . .)                                                                               
    Layer 3: pip install requirements.txt                                                                           
    Layer 2: prisma generate                                                                                        
    Layer 1: python:3.12-slim (base OS) 
    ```
- FastAPI swagger docker containers (btw: containers are inside it's own image)

## Monitoring

### Grafana
- Montiroing UI: Dashboard, send alerts, dashboards
- Port 3000

### Prometheus
- Monitoring DB (gets and stores metrics)
- Scrap metrics via /metrics from FastAPI swagger every 15s
- localhost only on 127.0.0.1:9090 without public access