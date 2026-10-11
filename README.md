# SystemInformation

**A modern, cross-platform system information dashboard built with Python and PySide6.**

SystemInformation is a desktop application designed to present system and hardware information through a clean graphical interface. The goal is to make essential system statistics easy to explore without relying entirely on terminal commands.

> **Development status:** Early development. Features and platform support may change as the project evolves.

## Features

* **Overview** — A central dashboard for essential system statistics.
* **CPU & Memory** — Monitor processor and memory usage.
* **Storage** — Explore disk and filesystem information.
* **Network** — Inspect network interfaces and traffic statistics.
* **Processes** — Browse running processes.
* **System Details** — View operating system, kernel, Python and uptime information.
* **Hardware Information** — Display available hardware details.
* **Dark Interface** — A dark desktop UI with a green accent theme.

Feature availability depends on the operating system and the information exposed by the system.

## Screenshots

Screenshots will be added here as the interface develops.

## Technology Stack

* Python
* PySide6 / Qt for Python
* psutil
* PyInstaller for executable packaging

## Requirements

* Python 3.12 or newer, subject to dependency compatibility
* PySide6
* psutil
* Additional system utilities may be needed for certain hardware details on Linux

## Run from Source

Clone the repository:

```bash
git clone git@github.com:porialinux/systemmanitor.git
cd systemmanitor
```

Install the Python dependencies:

```bash
python -m pip install PySide6 psutil
```

Run the application:

```bash
python app.py
```

If your system uses an externally managed Python environment, create a virtual environment before installing dependencies.

## Build

Executable packaging is under development.

PyInstaller can be used to package the application for the operating system on which the build is performed. Platform-specific testing and packaging configuration are still required for reliable releases.

## Cross-Platform Roadmap

* [ ] Initial Python application
* [ ] Graphical interface with PySide6
* [ ] Improve hardware detection across platforms
* [ ] Linux AppImage release
* [ ] Windows executable release
* [ ] macOS application release
* [ ] Automated builds with GitHub Actions
* [ ] Screenshots and release documentation

## Contributing

Contributions, bug reports and feature suggestions are welcome.

When reporting a bug, include:

* Your operating system and version
* Your Python version
* Steps to reproduce the issue
* Relevant error messages

## License

A license has not been selected yet. Licensing information will be added once the project license is chosen.

---

**SystemInformation** — System details, clearly presented.
