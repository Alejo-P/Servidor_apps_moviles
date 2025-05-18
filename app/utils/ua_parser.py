from fastapi import Request
from user_agents import parse

def get_device_info(request: Request):
    ua_string = request.headers.get("user-agent", "")
    user_agent = parse(ua_string)

    return {
        "browser": f"{user_agent.browser.family} {user_agent.browser.version_string}",
        "os": f"{user_agent.os.family} {user_agent.os.version_string}",
        "device": user_agent.device.family,
        "is_mobile": user_agent.is_mobile,
        "is_tablet": user_agent.is_tablet,
        "is_pc": user_agent.is_pc,
    }
