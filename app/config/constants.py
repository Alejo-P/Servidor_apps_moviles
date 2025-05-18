# Definición de roles
ROLE_ALL = "Todos"
ROLE_ADMIN = "Administrador"
ROLE_USER = "Usuario"
ROLE_DEV = "Desarrollador"
ROLE_GUEST = "Invitado"

# Definición de entornos de desarrollo
ENV_DEVELOPMENT = "development"
ENV_PRODUCTION = "production"

# Definición de permisos
PERMISSIONS = {
    "file": [
        "upload",
        "list_own",
        "list_all",
        "delete_own",
        "delete_any",
        "view_own",
        "view_all"
    ],
    "qr": [
        "create_from_file",
        "create_from_text",
        "list_own",
        "list_all",
        "delete_own",
        "delete_any",
        "view_own",
        "view_all"
    ],
    "profile": [
        "update"
    ],
    "user": [
        "list",
        "create",
        "update",
        "deactivate"
    ],
    "role": [
        "assign",
        "remove",
        "crud"
    ],
    "dev": [
        "endpoints_list",
        "server_info",
        "logs_view"
    ],
    "password": [
        "change"
    ]
}