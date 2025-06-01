# Vertex

**Vertex** is a BitTorrent tracker in Python.

## Features

- HTTP/UDP tracker
- Private/public modes
- Highly configurable
- In-memory/sqlite3 database. Modular.

### Requires

- Python 3.7 or higher  
- [Poetry](https://python-poetry.org/) for dependency management  

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/tbwcjw/vertex.git
   cd vertex
   ```

2. Install dependencies using Poetry:

   ```bash
   poetry install
   ```

3. Configure the tracker by copying the sample configuration file:

   ```bash
   cp config.yaml.sample config.yaml
   ```

   Edit `config.yaml` to suit your environment.

### Running the Tracker

To start the tracker:

```bash
poetry run python vertex.py
```
Or 
```bash
poetry run waitress-serve vertex
```
Or any other crazy thing your heart desires.

## Contributing

Contributions are welcomed. We have a [TODO](https://github.com/tbwcjw/vertex/blob/main/TODO.md) file for future features/ideas.

## License

This project is licensed under the MIT License. See [LICENSE](https://github.com/tbwcjw/vertex/blob/main/LICENSE).
