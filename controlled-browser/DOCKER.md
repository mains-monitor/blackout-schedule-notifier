# Docker Test Instructions

## Build and run the test in Docker:

```bash
# Build the image
docker-compose build

# Run the test
docker-compose up

# Or run in one command
docker-compose up --build
```

## Check results:

The extracted JSON files will be saved to `./output/` directory.

```bash
ls -la output/
```

## Debugging:

To keep the container running for debugging:

1. Uncomment the `command: tail -f /dev/null` line in `docker-compose.yml`
2. Run: `docker-compose up -d`
3. Enter container: `docker exec -it schedule-extractor-test bash`
4. Run test manually: `python test_schedule_extractor.py`

## Clean up:

```bash
# Stop and remove container
docker-compose down

# Remove image
docker rmi controlled-browser-schedule-extractor
```
