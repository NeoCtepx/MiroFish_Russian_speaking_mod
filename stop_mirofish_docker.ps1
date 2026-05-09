$ErrorActionPreference = "Stop"
docker compose -p mirofish-nvidia -f C:\MiroFish\docker-compose.nvidia.yml down --remove-orphans
