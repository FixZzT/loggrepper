# Changelog

Todas las versiones notables de loggrepper documentadas aca.

El formato sigue [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
