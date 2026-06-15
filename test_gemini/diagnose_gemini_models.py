import os
import json
import warnings
from typing import Any, Dict, List

# Match ai_assistant.py behavior (ignore FutureWarnings etc.)
warnings.filterwarnings("ignore", category=FutureWarning)

# Load .env from Django BASE_DIR/.env (same convention as ai_assistant.py)
try:
    from django.conf import settings
    from dotenv import load_dotenv

    env_path = settings.BASE_DIR / ".env"
    load_dotenv(env_path, override=False)
except Exception:
    # If Django isn't configured (standalone use), try local .env next to manage.py
    # This is best-effort; the app itself is the source of truth.
    if not os.getenv("GEMINI_API_KEY"):
        candidate = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        try:
            from dotenv import load_dotenv

            load_dotenv(candidate, override=False)
        except Exception:
            pass

# Now import SDK
import google.generativeai as genai


def get_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def configure_genai() -> None:
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY missing. Expected it in .env at Django BASE_DIR/.env"
        )
    genai.configure(api_key=key)


def main() -> None:
    configure_genai()

    models: List[Any] = list(genai.list_models())

    out: Dict[str, Any] = {
        "count": len(models),
        "models": [],
    }

    for m in models:
        name = getattr(m, "name", None) or getattr(m, "model", None) or str(m)

        # Best-effort capability detection: different SDK versions expose different fields.
        # We do not fail discovery if capability introspection is unavailable.
        caps: Dict[str, Any] = {}
        for attr in [
            "supported_generation_methods",
            "supported_generation_types",
            "supportedGenerationMethods",
            "capabilities",
            "generation_config",
        ]:
            if hasattr(m, attr):
                try:
                    caps[attr] = getattr(m, attr)
                except Exception:
                    pass

        out["models"].append({"name": name, "capabilities": caps})

    # Print ALL available models (required)
    print("ALL AVAILABLE MODELS:")
    for item in out["models"]:
        print(item["name"])

    # Also dump as JSON for programmatic parsing
    print("\nJSON_DUMP_START")
    print(json.dumps(out, indent=2, default=str))
    print("JSON_DUMP_END")


if __name__ == "__main__":
    main()

