<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/README-Principal-047857?style=flat-square" alt="README principal" /></a>
</p>

# Cómo correr Luuka

### Levantar la app con Docker

Necesitas [Docker](https://docs.docker.com/get-docker/) con Docker Compose.

1. Copia el archivo de configuración:

   ```bash
   cp .env.example .env
   ```

2. Abre `.env` y cambia estos dos valores:
   - `POSTGRES_PASSWORD`: la contraseña de la base de datos. No uses `@ : / ?`, porque va dentro de una URL.
   - `SECRET_KEY`: la llave para firmar los tokens. Puedes generar una con `openssl rand -hex 32`.

3. Levanta todo (base de datos, backend y frontend):

   ```bash
   docker compose up --build
   ```

4. Abre la app en http://localhost:5173. La API queda en http://localhost:8000 y su documentación en http://localhost:8000/docs.

Para probar la división de la cancha necesitas al menos dos cuentas. Puedes abrir la segunda en una ventana de incógnito.

Para detener todo usa `docker compose down`. Si además quieres borrar la base de datos, usa `docker compose down -v`.

### Revisar que los saldos cuadren

Con la app corriendo, este comando recalcula el saldo de cada cuenta a partir de sus movimientos y revisa que la suma de todos los saldos sea igual a todo lo recargado:

```bash
docker compose exec backend python -m app.db.check_balances
```

Si todo cuadra, lo dice y termina bien. Si algo no cuadra, muestra qué cuenta tiene el problema y termina con error.

## Correr los tests

Los tests se corren con Python 3.12, desde la carpeta `backend/`.

### Preparar el entorno

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### Todos los tests

```bash
python -m pytest
```

Por defecto usan SQLite en memoria, así que no hace falta tener una base de datos. Los dos tests de operaciones al mismo tiempo aparecen como `skipped`, porque necesitan PostgreSQL (ver la siguiente sección).

### Con PostgreSQL

Los bloqueos de filas (`SELECT ... FOR UPDATE`) solo existen en PostgreSQL. Para correr también los tests que los prueban, levanta una base de PostgreSQL aparte, solo para los tests:

```bash
docker run --rm -d --name luuka-test-db -p 5433:5432 \
  -e POSTGRES_PASSWORD=test -e POSTGRES_DB=luuka_test postgres:17-alpine
```

Espera unos segundos a que arranque y corre los tests apuntando a esa base:

```bash
export TEST_DATABASE_URL=postgresql+psycopg://postgres:test@localhost:5433/luuka_test
python -m pytest
```

> Los tests borran todo lo que haya en la base de `TEST_DATABASE_URL`. Nunca la apuntes a la base de la app.

Cuando termines, apaga la base de pruebas con `docker stop luuka-test-db`. Como se creó con `--rm`, se borra sola.

Para correr solo los tests que necesitan PostgreSQL:

```bash
python -m pytest -m postgres -v
```

## Tests por caso

Cada comando corre solo los tests de un caso. Con `-v` se ve el nombre de cada test y si pasó.

### No se cobra dos veces

Si la misma operación llega dos veces con la misma `Idempotency-Key`, se aplica una sola vez. Si un jugador paga dos veces su parte de la cancha, solo se le cobra una vez.

```bash
python -m pytest -v -k "applied_once or creates_it_once or twice_charges_only_once"
```

| Test                                                                       | Qué prueba                                                   |
| -------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `test_reload_retry_with_same_idempotency_key_is_applied_once`              | Una recarga repetida suma el dinero una sola vez.            |
| `test_transfer_retry_with_same_idempotency_key_is_applied_once`            | Una transferencia repetida descuenta el dinero una sola vez. |
| `test_create_group_charge_retry_with_same_idempotency_key_creates_it_once` | Un cobro de cancha repetido se crea una sola vez.            |
| `test_pay_member_charge_twice_charges_only_once`                           | Pagar dos veces la misma parte cobra una sola vez.           |

### Sin saldo suficiente no se mueve nada

Si alguien no tiene saldo para transferir o pagar su parte, la operación se rechaza y ningún saldo cambia.

```bash
python -m pytest -v -k "insufficient_funds"
```

| Test                                                                             | Qué prueba                                                              |
| -------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `test_transfer_with_insufficient_funds_returns_400_and_keeps_balances`           | La transferencia se rechaza y los dos saldos quedan igual.              |
| `test_pay_member_charge_with_insufficient_funds_returns_400_and_changes_nothing` | El pago se rechaza, los saldos quedan igual y la parte sigue pendiente. |

### Operaciones al mismo tiempo (bloqueos)

Cuando llegan varias operaciones al mismo tiempo sobre las mismas cuentas, cada una espera a la anterior y ninguna gasta dinero que no hay. Dos de estos tests necesitan PostgreSQL (ver [Con PostgreSQL](#con-postgresql)). Sin él, aparecen como `skipped`.

```bash
python -m pytest -v -k "under_lock or concurrent"
```

| Test                                                                    | Qué prueba                                                                                                                     | Necesita PostgreSQL |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | :-----------------: |
| `test_transfer_uses_balance_read_under_lock_not_stale_one`              | Una transferencia usa el saldo real del momento, no uno viejo que ya estaba cargado en memoria.                                |         No          |
| `test_concurrent_transfers_in_both_directions_keep_balances_consistent` | 40 transferencias al mismo tiempo entre dos cuentas, en las dos direcciones, dejan los saldos correctos y sin bloqueos mutuos. |         Sí          |
| `test_concurrent_payments_of_all_members_complete_the_group_charge`     | 8 jugadores pagando su parte al mismo tiempo: el cobro queda completado y el creador recibe exactamente el total.              |         Sí          |

### Los saldos cuadran con sus movimientos

El saldo de cada cuenta es igual a lo que entró menos lo que salió, y la suma de todos los saldos es igual a lo recargado.

```bash
python -m pytest -v tests/test_reconciliation.py
```

| Test                                                                    | Qué prueba                                                                                                    |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `test_balances_match_their_movements_after_every_kind_of_operation`     | Después de recargas, transferencias, reintentos, una transferencia rechazada y un pago repetido, todo cuadra. |
| `test_check_balances_finds_a_balance_that_does_not_match_its_movements` | Si un saldo se cambia sin un movimiento (simulando un error), la revisión lo detecta.                         |
| `test_check_balances_with_no_accounts_is_consistent`                    | Sin cuentas, todo cuadra en cero.                                                                             |
| `test_check_balances_command_fails_only_when_something_does_not_match`  | El comando termina bien si todo cuadra y con error si algo no cuadra.                                         |

### La división de la cancha siempre suma el total

Al dividir en pesos enteros no se pierde ni sobra ningún peso, con y sin el creador jugando.

```bash
python -m pytest -v -k "split"
```

### Los montos inválidos se rechazan

Montos con decimales, como texto (por ejemplo `"50.000"`) o por fuera de los límites se rechazan.

```bash
python -m pytest -v -k "invalid_amount or invalid_total or whole_peso"
```
