import json
import os
import threading
from flask import request, has_request_context

_thread_local = threading.local()
_locales_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'locales')

def _load_json(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def _safe_locale(raw):
    if not raw:
        return 'en'
    raw = str(raw).split(',')[0].split(';')[0].split('-')[0].strip().lower()
    return raw or 'en'

try:
    _languages = _load_json(os.path.join(_locales_dir, 'languages.json'))
except Exception:
    _languages = {'en': {'label': 'English', 'llmInstruction': 'Please respond in English.'}}

_translations = {}
if os.path.isdir(_locales_dir):
    for filename in os.listdir(_locales_dir):
        if filename.endswith('.json') and filename != 'languages.json':
            locale_name = filename[:-5]
            try:
                _translations[locale_name] = _load_json(os.path.join(_locales_dir, filename))
            except Exception:
                pass

def set_locale(locale: str):
    _thread_local.locale = _safe_locale(locale)

def get_locale() -> str:
    if has_request_context():
        raw = request.headers.get('Accept-Language', 'en')
        loc = _safe_locale(raw)
        return loc if loc in _translations else 'en'
    loc = getattr(_thread_local, 'locale', 'en')
    return loc if loc in _translations else 'en'

def t(key: str, **kwargs) -> str:
    locale = get_locale()
    messages = _translations.get(locale, _translations.get('en', {}))
    value = messages
    for part in key.split('.'):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = None
            break
    if value is None:
        return key
    if kwargs and isinstance(value, str):
        for k, v in kwargs.items():
            value = value.replace(f'{{{k}}}', str(v))
    return value

def get_language_instruction() -> str:
    locale = get_locale()
    lang_config = _languages.get(locale, _languages.get('en', {}))
    return lang_config.get('llmInstruction', 'Please respond in English.')
