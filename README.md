# fuelfam

The API listens on port 8000. Upload state stays in memory and is lost when the container stops.

Set `ANTHROPIC_API_KEY` and `GOOGLE_MAPS_API_KEY` before starting. For a local run, copy `.env.example` to `.env` and fill in both values.

## Run locally

```bash
docker compose up --build
```

## Run in production

```bash
docker build -t fuelfam .
docker run --rm -p 8000:8000 \
  -e ANTHROPIC_API_KEY -e GOOGLE_MAPS_API_KEY \
  fuelfam
```

The production command forwards those two variables from the shell into the container.
