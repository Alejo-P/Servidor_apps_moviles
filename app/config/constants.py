# Definición de roles
ROLE_ALL = "Todos"
ROLE_ADMIN = "Administrador"
ROLE_USER = "Usuario"
ROLE_GUEST = "Invitado"

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