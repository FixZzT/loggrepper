# Contribuir a loggrepper

Gracias por tu interes en contribuir.

## Setup de desarrollo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Antes de enviar cambios

- El codigo pasa `ruff check src/ tests/`
- El codigo pasa `mypy src/`
- Los tests pasan: `pytest`
- Los commits siguen el formato: `tipo(scope): mensaje`

## Reportar bugs

Usa el template de bug report en GitHub Issues. Inclui el comando exacto, archivo de entrada y output esperado vs obtenido.

## Pull requests

1. Crea un branch desde `main`
2. Hace los cambios con tests
3. Asegurate de que CI pase
4. Abri PR con descripcion de que y por que

Las PRs se mergean con squash a main.
