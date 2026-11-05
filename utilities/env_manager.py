import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger("SignatureAutomation")

def update_env_with_all_users(users: list, env_file_path: Path):
    """
    Completely rewrite the USER_* section of .env using two-digit indexing (USER_01_NAME, etc.).
    Preserves static Admin variables (BASE_URL, BASE_API_URL, EMAIL, PASSWORD) and removes all previous USER_* entries.
    """
    env_file_path = Path(env_file_path).resolve()
    if not env_file_path.exists():
        env_file_path.touch()

    # 1. Read existing lines and preserve static Admin variables only
    with open(env_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    static_keys = {
        "BASE_URL", "BASE_API_URL", "EMAIL", "PASSWORD",
        "stg_api_baseurl", "STG_API_BASEURL", "STG_API_URL", "STG_URL",
        "prod_api_baseurl", "PROD_API_BASEURL", "PROD_API_URL", "PROD_URL"
    }
    static_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if any(stripped.startswith(f"{key}=") for key in static_keys):
            static_lines.append(stripped + "\n")

    # 2. Build new USER_* section in exact requested format with two-digit indexing
    user_lines = []
    for idx, user in enumerate(users, start=1):
        fmt = f"{idx:02d}"

        raw_name = str(user.get("name", "")).replace("\n", " ").strip()
        raw_email = str(user.get("email", "")).replace("\n", " ").strip()
        raw_role = str(user.get("role", "")).replace("\n", ", ").strip()

        clean_name = raw_name if raw_name else "NA"
        clean_email = raw_email if raw_email else "NA"
        clean_role = raw_role if raw_role else "NA"

        user_lines.append(f"USER_{fmt}_NAME={clean_name}\n")
        user_lines.append(f"USER_{fmt}_EMAIL={clean_email}\n")
        user_lines.append(f"USER_{fmt}_PASSWORD=123456\n")
        user_lines.append(f"USER_{fmt}_ROLE={clean_role}\n")

    # 3. Rewrite .env file completely with no blank lines between user records
    final_content = "".join(static_lines) + ("\n" if static_lines else "") + "".join(user_lines)

    with open(env_file_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    # 4. Reload environment variables with override
    load_dotenv(dotenv_path=env_file_path, override=True)
