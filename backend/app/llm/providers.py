import os
import time
import random
import requests

def _post(url: str, headers: dict, payload: dict) -> str:
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def openai_chat(messages: list[dict]) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return _post("https://api.openai.com/v1/chat/completions",
                 {"Authorization": f"Bearer {key}"},
                 {"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "messages": messages})



def openrouter_chat(messages: list[dict]) -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    model = os.getenv("OPENROUTER_MODEL", "openrouter/free")

    return _post(
        "https://openrouter.ai/api/v1/chat/completions",
        {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "AI Interview Platform"
        },
        {
            "model": model,
            "messages": messages
        }
    )





def gemini_chat(messages: list[dict]) -> str:
    key = os.getenv("GEMINI_API_KEY")

    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    model = model.strip().removeprefix("models/")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent"
    )

    # Convert messages into Gemini-compatible contents.
    system_instruction = ""
    contents = []

    for message in messages:
        role = message.get("role", "user")
        content = str(message.get("content", ""))

        if role == "system":
            system_instruction += content + "\n"
        else:
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })

    payload = {"contents": contents}

    if system_instruction.strip():
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction.strip()}]
        }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": key
    }

    # Retry temporary server and quota errors.
    retry_statuses = {429, 500, 502, 503, 504}
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=90
            )

            if response.status_code in retry_statuses:
                if attempt < max_attempts - 1:
                    retry_after = response.headers.get("Retry-After")

                    try:
                        delay = float(retry_after) if retry_after else 2 ** (attempt + 1)
                    except ValueError:
                        delay = 2 ** (attempt + 1)

                    delay = min(delay, 30) + random.uniform(0, 1)
                    print(
                        f"Gemini temporarily unavailable "
                        f"(HTTP {response.status_code}). "
                        f"Retrying in {delay:.1f} seconds..."
                    )
                    time.sleep(delay)
                    continue

            if not response.ok:
                raise RuntimeError(
                    f"Gemini API error {response.status_code}: "
                    f"{response.text[:1000]}"
                )

            data = response.json()

            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError(
                    f"Gemini returned no candidates: {str(data)[:1000]}"
                )

            parts = candidates[0].get("content", {}).get("parts", [])
            answer = "".join(
                part.get("text", "")
                for part in parts
                if "text" in part
            )

            if not answer.strip():
                raise RuntimeError("Gemini returned an empty response")

            return answer

        except requests.RequestException as exc:
            if attempt == max_attempts - 1:
                raise RuntimeError(
                    f"Gemini connection failed after {max_attempts} attempts: {exc}"
                ) from exc

            delay = 2 ** (attempt + 1) + random.uniform(0, 1)
            print(f"Gemini connection problem. Retrying in {delay:.1f} seconds...")
            time.sleep(delay)

    raise RuntimeError("Gemini request failed after all retry attempts")
