# IMSUTH digital platforms

This repository keeps the public hospital website and the secured PayPoint application in separate application folders.

## Project structure

```text
website/   Public IMSUTH website and PayPoint UI source
backend/   Django PayPoint business logic, APIs and deployment configuration
docs/      Shared architecture, security, deployment and approval documents
```

The public website deployment workflows copy only allowlisted files from `website/`. They do not publish the Django backend, local databases, environment files or PayPoint documentation.

The PayPoint UI is stored at `website/paypoint/` and is rendered securely by Django. For PayPoint development and verification, work from `backend/` and follow `backend/README.md`.


## Live frontend and local API

See [Live UI connections](docs/paypoint/LIVE-UI-CONNECTIONS.md) for connected workflows, local startup and verification. The port 5500 entry point requires `backend/dev_proxy.py` alongside Django on port 8012; it no longer uses demo responses.
