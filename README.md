# Astra

A Python bot for the Builders Mech Royale competition. Astra aims for placement in a 16-mech free-for-all. Its initial policy heads inside the next safe circle, strafes around nearby attackers, and picks up weapons within reach. It can move and aim independently.

## Runtime and attribution

The root Dockerfile pins CPython 3.13.18 on Debian Trixie by digest. The bot uses only the Python standard library. The JSON-lines transport and type definitions in `mechfight.py` come from the official Builders starter kit. The kit's example and Dockerfile supplied the starting layout. The referee mounts the organizer's map at runtime.

[Organizer’s starter kit and protocol](https://www.joinbuilders.org/buildathon/tracks/builders)

## Run the official replay check

From the extracted kit directory, set `BOT` to the absolute path to this checkout. Make the map readable by the container user.

```sh
chmod -R a+rX arena
python3 check/check.py -- python3 -u "$BOT/bot.py"
docker build --platform linux/amd64 -t mech-royale-bot "$BOT"
python3 check/check.py --map-dir /arena -- docker run --rm -i --network none --cpus 1 --memory 512m --read-only --tmpfs /tmp:rw,size=64m --user 65534:65534 -v "$PWD/arena:/arena:ro" mech-royale-bot
```

The checker replays 300 observations and measures response timing. The competition site runs the 48 matches that determine a practice score. Use `git rev-parse HEAD` to identify the candidate for submission.
