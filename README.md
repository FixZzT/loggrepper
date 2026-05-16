# loggrepper

grep contextual para logs. Extrae ventanas de tiempo alrededor de matches en archivos de log — no por numero de lineas, sino por timestamps.

## El problema

`grep ERROR app.log` te da esto:

```
2026-05-16 14:32:01.123 ERROR PaymentProcessor: timeout
```

Pero no te dice **que paso antes** del error (¿llegó el request? ¿qué parámetros tenía?) ni **después** (¿se reintentó? ¿el usuario recibió 500?).

`grep -B 20 -A 20` asume que 20 lineas cubren tu ventana de tiempo. Si el request empezó 2 segundos antes y tu log es verboso, 20 lineas puede ser muy poco. Si es poco verboso, 20 lineas es ruido innecesario.

**loggrepper** busca por timestamps reales. Le pasai `--window 3s` y te devuelve todas las lineas cuyo timestamp está dentro de ±3 segundos del match. Lineas sueltas se agrupan en "incidentes". Ventanas solapadas se mergean.

## Instalacion

```bash
pip install git+https://github.com/FixZzT/loggrepper.git
# o modo desarrollo (editable)
pip install -e .
# o global con pipx
pipx install git+https://github.com/FixZzT/loggrepper.git
```

## Uso

```bash
# Basico
loggrepper ERROR app.log

# Ventana de 5 segundos
loggrepper ERROR app.log -w 5

# Salida JSON para scripts
loggrepper ERROR app.log -o json | jq '.[] | {start, end, line_count}'

# Formato de timestamp especifico
loggrepper "404" nginx-access.log --ts-format nginx

# Pipe desde docker/k8s
docker logs mi-app 2>&1 | loggrepper FATAL -
kubectl logs pod-xyz | loggrepper panic -
```

## Ejemplos reales

**Debuggear un error en produccion:**

```bash
$ loggrepper "IntegrityError" app.log -w 5

--- Incidente #1 | 14:32:00 — 14:32:04 | 5 lineas ---
    14:32:00.100 INFO  POST /api/orders payload={"user":42}
    14:32:00.500 DEBUG INSERT INTO orders VALUES (...)
>>> 14:32:01.123 ERROR IntegrityError: duplicate key
    14:32:01.200 WARN  rolling back transaction
    14:32:02.000 INFO  POST /api/orders -> 500
```

Veí el request entero, SQL, error, rollback, y respuesta — en contexto temporal real.

**Investigar timeouts entre microservicios:**

```bash
$ loggrepper "pi_abc123" payment-service.log -w 10

--- Incidente #1 | 14:32:00 — 14:32:10 | 7 lineas ---
    14:32:00.100 INFO  received payment intent pi_abc123
    14:32:00.200 DEBUG calling Stripe /v1/payment_intents
>>> 14:32:08.500 ERROR timeout calling Stripe (8.3s)
    14:32:08.501 WARN  retrying (1/3)
    14:32:10.000 DEBUG Stripe responded 200 OK
```

Stripe tardó 8s, no es tu codigo. La ventana captura causa y efecto.

**Auditar requests sospechosos en nginx:**

```bash
$ loggrepper "POST /admin" access.log --ts-format nginx -w 30 -o json | jq .
```

## Formatos de timestamp soportados

| Formato   | Ejemplo                                    | Uso tipico              |
|-----------|--------------------------------------------|--------------------------|
| iso8601   | `2026-05-16 14:32:01.123 ERROR`            | Python, Java, Node, Go   |
| iso8601-t | `2026-05-16T14:32:01.123Z ERROR`           | JSON logs, Docker, k8s   |
| syslog    | `May 16 14:32:01 hostname error:`          | syslog, journald, /var/log |
| nginx     | `16/May/2026:14:32:01 +0000 GET /`         | Nginx, Apache access     |
| epoch-ms  | `1715872321123 ERROR`                      | Splunk, sistemas embedded |

Con `--ts-format auto` (default) detecta automaticamente el formato analizando las primeras 50 lineas.

## Output

**Pretty** (default):

```
--- Incidente #1 | 2026-05-16 14:31:58 — 2026-05-16 14:32:04 | 5 lineas ---
    2026-05-16 14:32:00.100 INFO  inicio del proceso
>>> 2026-05-16 14:32:01.123 ERROR timeout en conexion
    2026-05-16 14:32:02.000 DEBUG conexion exitosa
```

`>>>` marca las lineas que matchean el patron. Cada incidente muestra rango temporal y cantidad de lineas.

**JSON**: cada incidente con id, start, end, lineas con numero, texto y flag `match`.

## Desarrollo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pytest            # 14 tests
ruff check src/ tests/
```
