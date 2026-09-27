<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/README-Principal-047857?style=flat-square" alt="README principal" /></a>
</p>

# Luuka - Backend

API de una billetera digital. Permite:

- Crear una cuenta e iniciar sesión.
- Recargar saldo.
- Transferir dinero a otra cuenta.
- Consultar el saldo y el historial de movimientos.
- Dividir el pago de una cancha entre varias personas con **cobros grupales**.

---

## ¿Qué necesito?

| Herramienta | Versión         | Para qué          |
| ----------- | --------------- | ----------------- |
| Python      | 3.12 o superior | Ejecutar la API   |
| PostgreSQL  | 14 o superior   | Guardar los datos |

---

## ¿Cómo funciona la autenticación?

Casi todos los endpoints necesitan saber **quién** hace la petición. Para eso se usa un **token** que recibes al iniciar sesión:

1. Creas tu cuenta con email y contraseña.
2. Inicias sesión y la API te entrega un token.
3. Envías ese token en cada petición, en el header `Authorization: Bearer <token>`.
4. El token vence a los 30 minutos (configurable). Cuando vence, vuelves a iniciar sesión.

```mermaid
sequenceDiagram
    actor U as Usuario (app)
    participant API as API Luuka
    participant DB as Base de datos

    U->>API: POST /accounts (nombre, email, contraseña)
    API->>DB: Guarda la cuenta (la contraseña se guarda cifrada)
    API-->>U: 201 Cuenta creada

    U->>API: POST /accounts/login (email, contraseña)
    API->>DB: Verifica la contraseña
    API-->>U: 200 { access_token }

    U->>API: GET /accounts/me/balance<br/>Authorization: Bearer TOKEN
    API->>API: Valida el token y sabe quién eres
    API->>DB: Consulta tu saldo
    API-->>U: 200 { balance }
```

---

## Endpoints

🔒 = necesita token.

| Método | Ruta                                        | Qué hace                                                   |
| ------ | ------------------------------------------- | ---------------------------------------------------------- |
| GET    | `/health`                                   | Comprueba que la API está encendida                        |
| POST   | `/accounts`                                 | Crea una cuenta                                            |
| POST   | `/accounts/login`                           | Inicia sesión y entrega un token                           |
| GET    | `/accounts/me` 🔒                           | Muestra tus datos: nombre, email, placa y saldo            |
| GET    | `/accounts/lookup?plate=KQX482` 🔒          | Busca una cuenta por su placa                              |
| GET    | `/accounts/me/balance` 🔒                   | Muestra tu saldo                                           |
| GET    | `/accounts/me/transactions` 🔒              | Muestra tu historial de movimientos                        |
| POST   | `/transactions/reloads` 🔒                  | Recarga saldo en tu cuenta                                 |
| POST   | `/transactions/transfers` 🔒                | Transfiere dinero a otra cuenta                            |
| POST   | `/group-charges` 🔒                         | Crea un cobro grupal y divide el total entre los miembros  |
| GET    | `/group-charges/created` 🔒                 | Muestra los cobros grupales que creaste (filtro `?state=`) |
| GET    | `/group-charges/{id}` 🔒                    | Muestra un cobro grupal y el estado de cada miembro        |
| GET    | `/group-charges/member-charges/me` 🔒       | Muestra tus cobros individuales (filtro `?state=PENDING`)  |
| POST   | `/group-charges/member-charges/{id}/pay` 🔒 | Paga tu parte de un cobro grupal                           |

---

## La placa: cómo encontrar a otra persona

Cada cuenta recibe al registrarse una **placa** única, con el formato de las placas de carro colombianas: 3 letras y 3 números, por ejemplo `KQX482`.

Para transferir o agregar a alguien a un cobro grupal:

1. La persona te dice su placa.
2. La app la busca con `GET /accounts/lookup?plate=KQX482`. También acepta minúsculas y guion: `kqx-482`.
3. La app muestra el nombre ("Beto Gómez") para que confirmes que es la persona correcta.
4. La app usa el `id` que devolvió la búsqueda para transferir o crear el cobro.

Tu propia placa aparece en `GET /accounts/me`.

---

## Cobros grupales

Sirven para dividir el pago de una cancha. Quien pagó la cancha (el **creador**) crea el cobro con el total y la lista de **miembros**. La API divide el total en partes iguales y crea un **cobro individual** para cada miembro. Cuando un miembro paga, el dinero pasa de su cuenta a la del creador. Cuando todos pagaron, el cobro grupal queda completado.

```mermaid
sequenceDiagram
    actor C as Creador (pagó la cancha)
    participant API as API Luuka
    actor M as Cada miembro

    C->>API: POST /group-charges<br/>total $100.000, miembros: Ana, Beto, Carla
    API-->>C: Cobro grupal PENDING<br/>Ana $33.334 · Beto $33.333 · Carla $33.333

    M->>API: GET /group-charges/member-charges/me?state=PENDING
    API-->>M: Tus cobros pendientes

    M->>API: POST /group-charges/member-charges/{id}/pay
    API->>API: Descuenta tu parte y se la abona al creador
    API-->>M: Tu cobro individual COMPLETED

    Note over API: Cuando el último miembro paga,<br/>el cobro grupal pasa a COMPLETED
```

**Reglas:**

- El creador no va en la lista de miembros. Si **también jugó**, envía `"creator_plays": true`: el total se divide entre los miembros **y él**, y su parte no se le cobra a nadie (la respuesta la muestra en `creator_share`). Por ejemplo, $100.000 entre 5 personas: cada uno de los 4 miembros paga $20.000 y el creador pone sus $20.000.
- Si no jugó (`creator_plays` es `false`, el valor por defecto), el total se divide solo entre los miembros y `creator_share` es 0.
- Si la división no es exacta:
  - Sin el creador, los pesos que sobran se reparten de a uno entre los primeros miembros de la lista. Por ejemplo, $100.000 entre 3 queda en $33.334, $33.333 y $33.333.
  - Con el creador, los pesos que sobran quedan en su parte, así ningún miembro paga más que los demás. Por ejemplo, $100.000 entre 2 miembros y el creador: cada miembro paga $33.333 y el creador pone $33.334.
- Crear el cobro **no mueve dinero**; el dinero se mueve cuando cada miembro paga. El pago aparece como `COURT_PAYMENT` en el historial.
- Solo el creador y los miembros pueden ver un cobro grupal.
- Pagar dos veces el mismo cobro individual **no cobra dos veces**: la segunda vez devuelve el cobro ya pagado.

**Estados:**

| Estado      | Cobro individual       | Cobro grupal                        |
| ----------- | ---------------------- | ----------------------------------- |
| `PENDING`   | El miembro aún no paga | Falta al menos un miembro por pagar |
| `COMPLETED` | El miembro ya pagó     | Todos los miembros pagaron          |

---

## ¿Qué es el header `Idempotency-Key`?

Sirve para que **una operación no se cobre dos veces** si la app la reenvía, por ejemplo cuando se cae el internet justo después de enviar una transferencia y la app no sabe si se hizo.

La app genera un código único cuando el usuario toca "Transferir" (o "Recargar", o "Crear cobro grupal") y lo envía en el header `Idempotency-Key`. Si ese mismo código vuelve a llegar, la API no repite la operación: devuelve la que ya hizo.

```mermaid
sequenceDiagram
    actor App
    participant API as API Luuka

    App->>API: Transferir $30.000 (Idempotency-Key: abc-123)
    API->>API: Descuenta $30.000 y guarda la operación
    API--xApp: ❌ La respuesta se pierde (sin internet)

    App->>API: Reintento: transferir $30.000 (Idempotency-Key: abc-123)
    API->>API: "abc-123 ya lo hice"
    API-->>App: ✅ 201 La misma transferencia (no se descuenta otra vez)
```

**Regla para la app:**

- **Misma clave** si no sabes si la operación funcionó: se cayó la red, hubo un timeout o un error 5xx.
- **Clave nueva** cuando el usuario inicia otra operación.
- Si reutilizas una clave con otros datos (otro monto u otro destino), la API responde `422`.

El header es opcional. Sin él, cada petición se procesa como una operación nueva.

---

## Errores: qué significa cada código

Todas las respuestas de error tienen la forma `{ "detail": "mensaje" }`.

| Código | Significado                                                                                                        |
| ------ | ------------------------------------------------------------------------------------------------------------------ |
| `400`  | La operación no se puede hacer (saldo insuficiente, transferencia a ti mismo, creador incluido como miembro)       |
| `401`  | Falta el token, es inválido o venció. También si el email o la contraseña son incorrectos                          |
| `404`  | La cuenta, la placa, el cobro grupal o el cobro individual no existe (o no tienes acceso)                          |
| `409`  | El email ya está registrado                                                                                        |
| `422`  | Los datos enviados no son válidos (por ejemplo, un monto fuera de los límites, con decimales o enviado como texto) |

---

## Conectar un frontend (CORS)

El navegador solo deja que una página llame a la API si su dirección está autorizada. Las direcciones permitidas se configuran en el `.env`, separadas por coma:

```
CORS_ORIGINS=http://localhost:5173,https://mi-frontend.com
```

Por defecto se permite `http://localhost:5173`, la dirección donde corre un frontend con Vite en desarrollo.

---

## Revisar que los saldos cuadren

El saldo de cada cuenta se puede recalcular a partir de sus movimientos: lo que entró menos lo que salió. Este comando hace esa revisión para todas las cuentas y, además, revisa que la suma de todos los saldos sea igual a todo lo recargado:

```bash
python -m app.db.check_balances
```

Con Docker: `docker compose exec backend python -m app.db.check_balances`.

Si todo cuadra, termina con código `0`. Si no, muestra las cuentas con descuadre y termina con código `1`. Solo lee: nunca corrige un saldo.

---

## Tests

### Instalar las herramientas de pruebas

```bash
pip install -r requirements-dev.txt
```

### Ejecutar los tests

Desde la carpeta `backend/`:

```bash
pytest
```

Por defecto los tests usan SQLite en memoria. Los dos tests de operaciones al mismo tiempo necesitan bloqueos de filas, que solo existen en PostgreSQL, así que con SQLite se omiten. Para correrlos, define `TEST_DATABASE_URL` con una base de PostgreSQL. **Esa base se borra.**

```bash
TEST_DATABASE_URL=postgresql+psycopg://usuario:clave@localhost:5432/luuka_test pytest
```

---

## Estructura del proyecto

```
backend/
├── app/
│   ├── main.py            # Punto de entrada de la API
│   ├── core/              # Configuración, seguridad, errores y autenticación
│   ├── db/                # Conexión a la base de datos, creación de tablas y revisión de saldos
│   ├── models/            # Tablas de la base de datos
│   ├── schemas/           # Formato de los datos que entran y salen de la API
│   ├── services/          # Lógica de negocio (cuentas, transacciones, cobros grupales, revisión de saldos)
│   └── routers/           # Endpoints
├── tests/                 # Pruebas automáticas
├── .env.example           # Plantilla de configuración
├── requirements.txt       # Dependencias de la API
└── requirements-dev.txt   # Dependencias para los tests
```
