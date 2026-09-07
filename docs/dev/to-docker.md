# Running Crossword Composer with Docker

Status: proposed design

## Goal

Package Crossword Composer so that a user can start it with:

```sh
docker compose up --build
```

The application should then be available at <http://localhost:5000>. Puzzles and
settings must survive container replacement and image upgrades.

This document is a design, not the implementation. It describes the files and
small application changes that should be added in a later change.

## Docker terms used here

- An **image** is the packaged application. It contains Python, the application,
  its Python libraries, the frontend files, and Chromium.
- A **container** is a running copy of the image. Containers are replaceable.
- A **bind mount** makes a host directory available inside a container. This
  design maps the repository's `docker-data/` directory to `/data` in the
  container. The database and settings therefore remain visible on the host.
- Docker Compose is the small configuration file that tells Docker how to build
  the image, publish the web port, and attach the bind mount.

The important rule is: application code goes in the image; user data goes in the
bind-mounted host directory.

## How the application works today

The current application is already a good fit for one container:

- `python -m crossword.http_server` starts the server.
- The same Python process serves the API and the files under `frontend/`.
- SQLite stores the puzzles in the file named by `dbfile`.
- The word list and optional grid archive are ordinary files named by
  `word_file` and `xdfile`.
- The configuration normally lives at `~/.config/crossword/config.yaml`.
- The Settings screen writes changes back to that configuration file.
- PDF exports start a local Chrome or Chromium process in headless mode.
- Definition lookup calls an Internet service at run time.

There is no separate frontend server or database server to containerize.

## Proposed layout

Inside the container, use these paths:

```text
/app                         read-only application files
/app/frontend                browser files served by Python
/app/samples/words.txt       bundled default word list
/app/samples/sample_grids.db bundled default grid archive
/data                        bind-mounted host data directory
/data/config.yaml            user-editable settings
/data/crossword.db           puzzle database
```

The repository layout on the host will include:

```text
docker-data/
  config.yaml
  crossword.db
```

Compose bind-mounts `./docker-data` at `/data`. The user can see, copy, and back
up the files without learning Docker volume commands. `docker-data/` must be
excluded from Git and from the Docker build context because it contains personal
data and changes while the application runs.

Only one container may use this directory at a time. This application is
single-user, and SQLite is not intended to be shared by several application
containers.

## Files to add

The implementation should add:

```text
Dockerfile
compose.yaml
.dockerignore
docker/config.yaml
docker/entrypoint.sh
```

The implementation should also add `docker-data/` to the repository's
`.gitignore`.

### `Dockerfile`

Use an official Python slim image whose Python version is supported by the
project. Python 3.12 on Debian Bookworm is a reasonable initial choice. Before a
release, pin the exact base-image digest so that a later rebuild cannot silently
change the operating system underneath the application.

The Dockerfile should:

1. Install Chromium, CA certificates, basic fonts, and `gosu` with `apt-get`.
2. Copy `pyproject.toml` and install the Python package with `pip`.
3. Copy `crossword/`, `frontend/`, `samples/`, and `docker/` into `/app`.
4. Create a non-root user, for example `crossword` with UID 10001.
5. Let the entrypoint prepare the bind-mounted `/data` directory.
6. Set `CROSSWORD_CONFIG=/data/config.yaml`.
7. Use the entrypoint to run `python -m crossword.http_server` as the non-root
   user.

An outline is:

```dockerfile
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CROSSWORD_CONFIG=/data/config.yaml

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates chromium fonts-liberation gosu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY crossword/ crossword/
COPY frontend/ frontend/
COPY samples/ samples/
COPY docker/ docker/
RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 crossword \
    && chmod +x /app/docker/entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["python", "-m", "crossword.http_server"]
```

The container starts its short entrypoint as root only so it can fix permissions
on a bind mount created by Docker. The entrypoint then uses `gosu` to replace
itself with the Python process running as `crossword`. The long-running
application must not run as root.

The exact Python image and installed Debian packages should be tested on every
CPU architecture the project supports. In particular, the Chromium package must
exist for that architecture.

### `docker/config.yaml`

This is the initial Docker-specific configuration:

```yaml
host: 0.0.0.0
port: 5000
dbfile: /data/crossword.db
xdfile: /app/samples/sample_grids.db
word_file: /app/samples/words.txt
log_level: INFO
message_line_timeout_ms: 2000
theme_color: "#154d71"
definition_provider: wiktionary
author_name: Your Name
author_address: "123 Main St, City, ST 12345"
author_email: you@example.com
```

`0.0.0.0` is necessary inside the container. It means “listen on every container
network address.” The Compose port rule below still limits access on the host to
the local computer.

The SQLite adapter creates a new database and its tables when
`/data/crossword.db` does not exist. The image therefore does not need to contain
a writable starter database.

### `docker/entrypoint.sh`

The entrypoint should create `/data` if needed, make it writable by the
`crossword` user, and copy `docker/config.yaml` to `/data/config.yaml` on first
start. It must never overwrite an existing config because that file may contain
settings saved by the user.

On Linux, files in a bind mount keep numeric user and group ownership. The
entrypoint should therefore change ownership of `docker-data/` and its existing
contents to UID and GID 10001 before starting Python. This is an intentional
host-side effect and must be mentioned in the user documentation. It avoids
asking a new Docker user to run a separate `chown` command. The entrypoint must
only change ownership below the exact `/data` mount.

Its final line should use `exec` and drop privileges:

```sh
exec gosu crossword:crossword "$@"
```

This lets stop and restart signals reach Python correctly.

### `compose.yaml`

Compose should build one service and attach the host data directory:

```yaml
services:
  crossword:
    build: .
    image: crossword-composer:local
    init: true
    restart: unless-stopped
    ports:
      - "127.0.0.1:5000:5000"
    environment:
      CROSSWORD_CONFIG: /data/config.yaml
    volumes:
      - type: bind
        source: ./docker-data
        target: /data
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - >-
          import urllib.request;
          urllib.request.urlopen('http://127.0.0.1:5000/api/config', timeout=2).read()
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

Run all Compose commands from the repository root. Relative bind-mount paths are
resolved from the Compose project directory, so `./docker-data` then has a
predictable meaning. Docker creates the directory if it is missing, and the
entrypoint initializes its permissions and config file.

Publishing `127.0.0.1:5000:5000` is intentional. The application has no login
screen, always acts as the same built-in user, and allows cross-origin API
requests. It must not be exposed directly to the public Internet.

A user who understands that risk may change the port rule to `5000:5000` to
make the application reachable from other computers on a trusted local network.
Public hosting needs authentication, HTTPS, and tighter CORS rules first.

### `.dockerignore`

Exclude files that do not belong in the image or make rebuilds unnecessarily
large:

```text
.git
.github
.pytest_cache
__pycache__
*.py[cod]
*.egg-info
.venv
venv
build
dist
docs
crossword/tests
docker-data
```

Do not exclude `frontend`, `samples`, or `docker`; the running image needs them.

## Small application change

Add support for a `CROSSWORD_CONFIG` environment variable in
`crossword.get_default_config_path()`:

```python
configured_path = os.environ.get("CROSSWORD_CONFIG")
if configured_path:
    return os.path.abspath(os.path.expanduser(configured_path))
```

This check should come before the Windows, macOS, and Linux default paths.

This one change is preferable to adding environment-variable handling for every
setting. It also makes the existing Settings screen work correctly: both startup
and settings updates refer to `/data/config.yaml`. Settings marked as requiring a
restart will continue to require a container restart.

Keep normal non-Docker behavior unchanged when `CROSSWORD_CONFIG` is absent.
Add unit tests for both the override and the existing default behavior.

## Dependency handling

`pyproject.toml` currently gives minimum names but does not lock exact versions.
That means two image builds on different days can install different dependency
versions. Before publishing images, create a reviewed constraints or lock file
and use it during `pip install`. Dependabot or a similar process can then update
those versions deliberately.

Chromium is a run-time dependency even though it is not a Python package. It is
needed for New York Times, solver, and solution PDF exports. A Docker smoke test
must exercise at least one PDF export; merely starting the server will not find a
missing Chromium installation.

The container needs outbound HTTPS access for definition lookup. Puzzle editing,
local word suggestions, and most imports and exports continue to work without
Internet access.

## Normal user workflow

After the implementation, the basic commands should be:

```sh
# Build and start in the background
docker compose up --build -d

# Show application logs
docker compose logs -f crossword

# Restart after changing a setting that requires restart
docker compose restart crossword

# Stop the application but keep all data
docker compose down
```

The user then opens <http://localhost:5000>.

`docker compose down` removes containers and networks but leaves
`./docker-data` alone. The `--volumes` option also does not delete bind-mounted
host files. The data is lost only if the user deletes `docker-data/` or its
contents, so user-facing documentation should clearly warn against doing that.

To upgrade:

1. Back up `docker-data/` while the application is stopped.
2. Obtain the new source or image.
3. Run `docker compose up --build -d` again.
4. Check the health status and logs.
5. Open an existing puzzle and verify it before removing the backup.

Compose replaces the container and mounts the same host directory into it.

## Existing users and backups

An existing user's `crossword.db` can be copied to
`docker-data/crossword.db` on the host. Do this while both the old application
and the Docker application are stopped. Copying a live SQLite database file can
produce an inconsistent backup because SQLite may also be using journal files.

The implementation should include simple backup and restore helper commands or
scripts. They should:

- stop the application or use SQLite's online backup API;
- archive both `docker-data/crossword.db` and `docker-data/config.yaml`;
- restore only into a stopped application;
- refuse to overwrite existing data unless the user explicitly confirms it;
- document that backups may contain puzzle content and personal author details.

With a bind mount, the simplest safe manual backup is to stop the application
and copy the entire `docker-data/` directory to a dated backup directory. A
restore replaces the contents of `docker-data/` while the application is
stopped. The implementation may later add scripts to make those steps less
error-prone.

Do not place the user's old host configuration into `docker-data/` unchanged.
Paths such as `/home/alice/words.txt` or `C:\Users\Alice\words.txt` do not exist
inside the container. Translate them to `/data/...` for user-owned files or
`/app/samples/...` for the bundled defaults.

The SQLite adapter performs its current compatibility updates during startup.
The database must therefore be backed up before the first start with a newer
image.

## Development workflow

The production image should contain copied code and should not mount the source
tree. That makes it repeatable and prevents local files from unexpectedly
changing a running container.

If live source mounting is useful during development, put it in a separate
`compose.dev.yaml`. The development override can mount the repository at `/app`
and run tests, but it should not change the production Compose file.

Run the existing unit test suite before building the production image. Then run
the HTTP and export smoke tests against the built image. The image tests catch
missing copied files and operating-system packages without requiring the
production image to include `pytest`.

## Verification plan

Automated checks should verify:

1. The image builds from a clean checkout.
2. After its short permission-setup step, the long-running application process
   runs as a non-root user.
3. The health check becomes healthy.
4. `/`, JavaScript, CSS, and `/api/config` are served.
5. A puzzle can be created, saved, closed, and reopened.
6. Restarting and recreating the container preserves that puzzle and settings in
   `docker-data/`.
7. A fresh `docker-data/` directory creates a usable empty database.
8. The default word list and grid generator work.
9. At least one supported file format can be imported and exported.
10. All three PDF exports succeed through Chromium.
11. A definition lookup succeeds when outbound Internet access is available and
    fails cleanly when it is unavailable.
12. `CROSSWORD_CONFIG` overrides the platform default without changing the
    default behavior for normal installations.

Also test upgrade and restore using a copy of a real older database. Never use
the only copy of a user's database for this test.

## Known limits and later improvements

- This design intentionally runs one process and one container. Scaling to
  several replicas would require replacing SQLite and revisiting the built-in
  single-user model.
- The current Python `HTTPServer` is suitable for the application's existing
  local, single-user use. Public deployment would need a separate security and
  production-serving design.
- The image will be fairly large because it includes Chromium. A later multi-stage
  build may reduce Python build leftovers, but Chromium itself will remain the
  largest part.
- Multi-architecture image publishing needs a PDF test on every architecture;
  successful Python installation alone is not enough.

## Acceptance criteria

The Docker conversion is complete when a new Docker user can follow the normal
workflow above, reach the application on localhost, use every export type, and
replace the container without losing settings or puzzles. The non-Docker startup
command must continue to work as it does today.
