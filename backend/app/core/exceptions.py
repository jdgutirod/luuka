from uuid import UUID

class DomainError(Exception):
    """Base class for business rule errors, independent of the HTTP layer."""


class AccountNotFoundError(DomainError):
    def __init__(self, account_id: UUID):
        self.account_id = account_id
        super().__init__(f"La cuenta {account_id} no existe")


class EmailAlreadyRegisteredError(DomainError):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"El email {email} ya está registrado")


class InvalidCredentialsError(DomainError):
    def __init__(self):
        super().__init__("Email o contraseña incorrectos")


class SameAccountTransferError(DomainError):
    def __init__(self):
        super().__init__("La cuenta de origen y la de destino deben ser distintas")


class InsufficientFundsError(DomainError):
    def __init__(self):
        super().__init__("Saldo insuficiente para realizar la transferencia")


class IdempotencyKeyConflictError(DomainError):
    def __init__(self, idempotency_key: str):
        self.idempotency_key = idempotency_key
        super().__init__(f"La clave de idempotencia '{idempotency_key}' ya se usó con otros datos")
