from fastapi import Request
from user_agents import parse


def _get_device(user_agent):
    """
    Devuelve una descripción más amigable del dispositivo detectado.
    """
    if user_agent.device.family == "Other":
        if user_agent.is_pc:
            return "Computadora de escritorio"
        elif user_agent.is_mobile:
            return "Dispositivo móvil"
        elif user_agent.is_tablet:
            return "Tablet"
        else:
            return "Dispositivo desconocido"
    return user_agent.device.family

def get_device_info(request: Request):
    ua_string = request.headers.get("user-agent", "")
    user_agent = parse(ua_string)

    return {
        "browser": f"{user_agent.browser.family} {user_agent.browser.version_string}",
        "os": f"{user_agent.os.family} {user_agent.os.version_string}",
        "device": _get_device(user_agent),
        "is_mobile": user_agent.is_mobile,
        "is_tablet": user_agent.is_tablet,
        "is_pc": user_agent.is_pc,
    }
