# Changelog

Todas las versiones notables de loggrepper documentadas aca.

El formato sigue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] — 2026-05-18

### Added

- `--before` / `--after`: ventanas asimetricas de contexto
- `--no-color`: desactivar colores en salida pretty
- `--idle-timeout`: salir tras N segundos sin datos en modo follow
- `-o ndjson`: salida NDJSON (un JSON por linea, streaming-friendly)
- Soporte para archivos comprimidos: `.gz`, `.bz2`, `.xz`
- `--version`: mostrar version de la herramienta
- API publica en `__init__.py` (Incident, LogLine, TimestampFormat, etc.)
- PEP 561: `py.typed` para soporte de type checkers
- Test coverage threshold en CI (85%)
- Tests de integracion CLI con CliRunner

### Fixed

- Redundancia entre formatos iso8601 e iso8601-t
- epoch-ms ahora valida que el año este en rango 2000-2100
- Buffer de pendientes truncado al exceder 10000 lineas
- Archivos comprimidos y stdin cierran correctamente
- Protocolo Formatter incluye `flush()` y `color` en PrettyFormatter

### Removed

- `matcher.py`: codigo muerto sin uso en produccion

## [0.2.0] — 2026-05-16

### Added

- Multi-patron: soporte para multiples patrones de busqueda simultaneos
- `--exclude` / `-e`: filtrar lineas con patron regex
- `--max-incidents` / `-n`: limitar cantidad de incidentes mostrados
- `--follow` / `-f`: modo tail -f para leer nuevas lineas en tiempo real
- `--output stats`: resumen estadistico en vez de incidentes individuales
- Colores con `rich` en salida pretty (matches en rojo, contexto en dim)
- Stdin via `-` como nombre de archivo
- mypy type checking en CI
- pytest-cov coverage en CI
- GitHub Actions workflow para publicar en PyPI al crear tag
- Issue templates (bug report, feature request)
- CONTRIBUTING.md y CHANGELOG.md

### Changed

- API interna de formateadores: `format_one` + `format_empty` en vez de `format`
- Protocolo `Formatter` actualizado con nuevos metodos

## [0.1.0] — 2026-05-16

### Added

- Primer release publico
- Busqueda con ventanas de tiempo en vez de lineas
- 5 formatos de timestamp: iso8601, iso8601-t, syslog, nginx, epoch-ms
- Auto-deteccion de formato
- Output pretty y JSON
- CI con matrix Python 3.10–3.14 + ruff lint
