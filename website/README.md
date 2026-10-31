# IMSUTH public website

This folder contains the public IMSUTH website:

- HTML pages
- CSS, images, icons, fonts and vanilla JavaScript under `assets/`
- approved public JSON content under `data/`
- PHP form handlers under `api/`
- public-site deployment examples under `deployment/`
- static PayPoint HTML, CSS and ES6 JavaScript under `paypoint/`

The root cPanel and GitHub deployment configurations publish an explicit allowlist of public-site files, including the static PayPoint interface. The PayPoint Django backend is isolated in `../backend/` and exposes authenticated API endpoints; all permissions and financial controls remain server-side.
