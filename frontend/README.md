<p align="center">
  <a href="../README.md"><img src="https://img.shields.io/badge/README-Principal-047857?style=flat-square" alt="README principal" /></a>
</p>

# Luuka - Frontend

Aplicación web de Luuka, pensada para usarse desde el celular. Sirve para manejar la billetera (recargar, transferir y ver movimientos) y para **dividir el pago de una cancha** entre quienes jugaron.

Todo lo que muestra y hace lo pide a la API del backend (ver [backend/README.md](../backend/README.md)).

A cada persona se le encuentra por su **placa**, por ejemplo `KQX-482`, que recibe al registrarse. La app nunca muestra el email ni el saldo de otra persona, solo su nombre y su placa.

## Vistas

### Sin sesión

| Vista          | Ruta        | Para qué sirve                                                  |
| -------------- | ----------- | --------------------------------------------------------------- |
| Iniciar sesión | `/login`    | Entrar con email y contraseña.                                  |
| Registro       | `/register` | Crear una cuenta. Al terminar ya quedas con la sesión iniciada. |

### Pestañas principales

Tienen una barra de navegación flotante abajo. El botón **+** del centro abre los atajos a Recargar, Transferir y Dividir una cancha.

| Vista       | Ruta            | Para qué sirve                                                                                                                                               |
| ----------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Inicio      | `/`             | Tu saldo y tu placa, accesos rápidos, un aviso si tienes cobros por pagar y tus últimos movimientos.                                                         |
| Movimientos | `/transactions` | Historial de recargas, transferencias y pagos de cancha, agrupado por día.                                                                                   |
| Cobros      | `/charges`      | Dos pestañas: **Por pagar**, con lo que te cobran y el botón para pagar tu parte, y **Creados por mí**, con los cobros que creaste y cuánto llevas recogido. |
| Perfil      | `/profile`      | Tus datos, tu placa para compartirla y el botón para cerrar sesión.                                                                                          |

### Pantallas de un paso a paso

No tienen la barra de abajo. Usan una flecha para volver y el botón principal siempre está en la parte inferior de la pantalla.

| Vista               | Ruta           | Para qué sirve                                                                                                                                        |
| ------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Recargar saldo      | `/reload`      | Agregar dinero a tu billetera, con montos sugeridos.                                                                                                  |
| Transferir          | `/transfer`    | Buscar a la persona por su placa, confirmar su nombre, elegir el monto y confirmar el envío.                                                          |
| Dividir una cancha  | `/charges/new` | Crear un cobro: nombre, total pagado, si **tú también jugaste** y las personas, agregadas por placa. Muestra cuánto pagará cada uno antes de crearlo. |
| Detalle de un cobro | `/charges/:id` | Estado del cobro, progreso de lo recogido y quién ya pagó. Si eres miembro y te falta pagar, desde aquí pagas tu parte.                               |
