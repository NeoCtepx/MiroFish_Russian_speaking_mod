
import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT = Path(r"C:\MiroFish")
COMPOSE = PROJECT / "docker-compose.nvidia.yml"
DOCKERFILE = PROJECT / "Dockerfile.local"
LLM_FILE = PROJECT / "backend" / "app" / "utils" / "llm_client.py"
FIXED_LLM_CODE = '"""OpenAI-compatible LLM client with NVIDIA JSON fallback."""\n\nimport json\nimport re\nfrom typing import Optional, Dict, Any, List\n\nfrom openai import OpenAI\n\nfrom ..config import Config\n\n\nclass LLMClient:\n    """LLM client."""\n\n    def __init__(\n        self,\n        api_key: Optional[str] = None,\n        base_url: Optional[str] = None,\n        model: Optional[str] = None,\n    ):\n        self.api_key = api_key or Config.LLM_API_KEY\n        self.base_url = base_url or Config.LLM_BASE_URL\n        self.model = model or Config.LLM_MODEL_NAME\n\n        if not self.api_key:\n            raise ValueError("LLM_API_KEY is not configured")\n\n        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)\n\n    def _is_nvidia(self) -> bool:\n        return "nvidia" in (self.base_url or "").lower()\n\n    def _clean_text(self, content: Optional[str]) -> str:\n        text = content or ""\n        text = re.sub(r"<think>[\\s\\S]*?</think>", "", text).strip()\n        return text\n\n    def _extract_json(self, text: str) -> Dict[str, Any]:\n        cleaned = (text or "").strip()\n        cleaned = re.sub(r"^```(?:json)?\\s*", "", cleaned, flags=re.IGNORECASE)\n        cleaned = re.sub(r"\\s*```$", "", cleaned).strip()\n\n        decoder = json.JSONDecoder()\n\n        try:\n            value, _ = decoder.raw_decode(cleaned)\n            if isinstance(value, dict):\n                return value\n            return {"items": value}\n        except Exception:\n            pass\n\n        starts = [pos for pos in (cleaned.find("{"), cleaned.find("[")) if pos >= 0]\n        if not starts:\n            raise ValueError("LLM returned no JSON: " + cleaned[:1000])\n\n        start = min(starts)\n        fragment = cleaned[start:]\n        try:\n            value, _ = decoder.raw_decode(fragment)\n            if isinstance(value, dict):\n                return value\n            return {"items": value}\n        except Exception as exc:\n            raise ValueError("LLM returned invalid JSON: " + cleaned[:1000]) from exc\n\n    def chat(\n        self,\n        messages: List[Dict[str, str]],\n        temperature: float = 0.7,\n        max_tokens: int = 4096,\n        response_format: Optional[Dict] = None,\n    ) -> str:\n        kwargs = {\n            "model": self.model,\n            "messages": messages,\n            "temperature": temperature,\n            "max_tokens": max_tokens,\n        }\n        if response_format:\n            kwargs["response_format"] = response_format\n\n        response = self.client.chat.completions.create(**kwargs)\n        content = response.choices[0].message.content\n        return self._clean_text(content)\n\n    def _chat_raw(\n        self,\n        messages: List[Dict[str, str]],\n        temperature: float,\n        max_tokens: int,\n        extra_body: Optional[Dict[str, Any]] = None,\n        response_format: Optional[Dict[str, Any]] = None,\n    ) -> str:\n        kwargs = {\n            "model": self.model,\n            "messages": messages,\n            "temperature": temperature,\n            "max_tokens": max_tokens,\n        }\n        if extra_body:\n            kwargs["extra_body"] = extra_body\n        if response_format:\n            kwargs["response_format"] = response_format\n\n        response = self.client.chat.completions.create(**kwargs)\n        return self._clean_text(response.choices[0].message.content)\n\n    def chat_json(\n        self,\n        messages: List[Dict[str, str]],\n        temperature: float = 0.3,\n        max_tokens: int = 4096,\n    ) -> Dict[str, Any]:\n        json_messages = [\n            {\n                "role": "system",\n                "content": "Return only valid JSON. Do not use markdown. Do not add explanations.",\n            }\n        ] + list(messages)\n\n        errors = []\n\n        if self._is_nvidia():\n            schema = {"type": "object", "additionalProperties": True}\n            try:\n                content = self._chat_raw(\n                    messages=json_messages,\n                    temperature=temperature,\n                    max_tokens=max_tokens,\n                    extra_body={"nvext": {"guided_json": schema}},\n                )\n                return self._extract_json(content)\n            except Exception as exc:\n                errors.append("nvidia guided_json failed: " + str(exc))\n\n            try:\n                content = self._chat_raw(\n                    messages=json_messages,\n                    temperature=temperature,\n                    max_tokens=max_tokens,\n                )\n                return self._extract_json(content)\n            except Exception as exc:\n                errors.append("plain json prompt failed: " + str(exc))\n        else:\n            try:\n                content = self._chat_raw(\n                    messages=json_messages,\n                    temperature=temperature,\n                    max_tokens=max_tokens,\n                    response_format={"type": "json_object"},\n                )\n                return self._extract_json(content)\n            except Exception as exc:\n                errors.append("json_object failed: " + str(exc))\n\n            try:\n                content = self._chat_raw(\n                    messages=json_messages,\n                    temperature=temperature,\n                    max_tokens=max_tokens,\n                )\n                return self._extract_json(content)\n            except Exception as exc:\n                errors.append("plain json prompt failed: " + str(exc))\n\n        raise ValueError("LLM JSON call failed. " + " | ".join(errors))\n'

def log(msg):
    print(msg, flush=True)

def fail(msg, code=1):
    print("[error] " + msg, flush=True)
    sys.exit(code)

def run(cmd, cwd=None, check=True):
    log("[run] " + " ".join(cmd))
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    if check and p.returncode != 0:
        fail("command failed with exit code %s: %s" % (p.returncode, " ".join(cmd)))
    return p.returncode

def write_text_utf8(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def patch_llm_client():
    if not LLM_FILE.exists():
        fail("llm_client.py not found: %s" % LLM_FILE)

    backup = LLM_FILE.with_suffix(".py.bak_targeted_fix")
    try:
        if not backup.exists():
            shutil.copy2(LLM_FILE, backup)
            log("[ok] Backup written: %s" % backup)
    except Exception as e:
        log("[warn] Could not write backup: %s" % e)

    write_text_utf8(LLM_FILE, FIXED_LLM_CODE)
    log("[ok] Patched %s" % LLM_FILE)

    run([sys.executable, "-m", "py_compile", str(LLM_FILE)], cwd=PROJECT)
    log("[ok] Python syntax check passed for llm_client.py")

def patch_dockerfile_procps():
    if not DOCKERFILE.exists():
        fail("Dockerfile.local not found: %s" % DOCKERFILE)

    text = DOCKERFILE.read_text(encoding="utf-8", errors="replace")
    if " procps" in text or "procps " in text or "install -y procps" in text:
        log("[ok] Dockerfile.local already contains procps")
        return

    addition = """

# Required by npm concurrently when it stops child processes.
RUN apt-get update && apt-get install -y procps && rm -rf /var/lib/apt/lists/*
"""
    DOCKERFILE.write_text(text.rstrip() + addition, encoding="utf-8", newline="\n")
    log("[ok] Added procps to Dockerfile.local")

def main():
    log("=== MiroFish targeted repair V15 ===")
    log("This patch changes only broken runtime files.")
    if not PROJECT.exists():
        fail("Project folder not found: %s" % PROJECT)
    if not COMPOSE.exists():
        fail("Compose file not found: %s" % COMPOSE)

    patch_llm_client()
    patch_dockerfile_procps()

    log("")
    log("=== Rebuild and restart only mirofish-nvidia ===")
    run(["docker", "compose", "-p", "mirofish-nvidia", "-f", str(COMPOSE), "down", "--remove-orphans"], cwd=PROJECT, check=False)
    run(["docker", "compose", "-p", "mirofish-nvidia", "-f", str(COMPOSE), "build"], cwd=PROJECT)
    run(["docker", "compose", "-p", "mirofish-nvidia", "-f", str(COMPOSE), "up", "-d"], cwd=PROJECT)

    log("")
    log("[ok] Targeted repair finished")
    log("Open: http://127.0.0.1:3000")
    log("Logs: docker compose -p mirofish-nvidia -f C:\\MiroFish\\docker-compose.nvidia.yml logs -f --tail=200")

if __name__ == "__main__":
    main()
