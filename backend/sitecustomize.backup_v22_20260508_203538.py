# v20_mirofish_user_char_guard
# Runtime-only guard for scripts/run_parallel_simulation.py.
# It fixes agent CSV/DataFrame schema when fallback synthetic Twitter profiles
# do not contain the column required by OASIS: user_char.
# This file is ASCII-only.

import os
import sys

def _is_parallel_sim_process():
    joined = " ".join(str(x) for x in sys.argv)
    return "run_parallel_simulation.py" in joined

def _stringify(value):
    try:
        if value is None:
            return ""
        if value != value:
            return ""
        return str(value)
    except Exception:
        return ""

def _build_user_char_for_row(row):
    keys = [
        "user_char",
        "persona",
        "personality",
        "description",
        "bio",
        "profile",
        "user_profile",
        "summary",
        "name",
        "user_name",
        "username",
        "screen_name",
        "id",
        "user_id",
    ]
    parts = []
    for key in keys:
        try:
            if key in row.index:
                val = _stringify(row.get(key, ""))
                if val:
                    parts.append(val)
        except Exception:
            pass
    text = " | ".join(parts).strip()
    if not text:
        text = "Synthetic fallback agent with neutral behavior, realistic social-media posting habits, and balanced opinions."
    return text

def _ensure_user_char_dataframe(df):
    try:
        import pandas as pd
        if not isinstance(df, pd.DataFrame):
            return df
        if "user_char" not in df.columns:
            try:
                df = df.copy()
                df["user_char"] = df.apply(_build_user_char_for_row, axis=1)
            except Exception:
                try:
                    df["user_char"] = "Synthetic fallback agent with neutral behavior and realistic social-media posting habits."
                except Exception:
                    pass
        else:
            try:
                empty_mask = df["user_char"].isna() | (df["user_char"].astype(str).str.strip() == "")
                if empty_mask.any():
                    df = df.copy()
                    df.loc[empty_mask, "user_char"] = df[empty_mask].apply(_build_user_char_for_row, axis=1)
            except Exception:
                pass
        return df
    except Exception:
        return df

if _is_parallel_sim_process():
    try:
        import pandas as pd

        _orig_read_csv = pd.read_csv
        _orig_getitem = pd.DataFrame.__getitem__

        def _patched_read_csv(*args, **kwargs):
            df = _orig_read_csv(*args, **kwargs)
            path = ""
            try:
                if args:
                    path = str(args[0])
                else:
                    path = str(kwargs.get("filepath_or_buffer", ""))
            except Exception:
                path = ""
            low = path.lower()
            if ("twitter" in low) or ("profile" in low) or ("agent" in low):
                df = _ensure_user_char_dataframe(df)
            return df

        def _patched_getitem(self, key):
            if key == "user_char":
                try:
                    if "user_char" not in self.columns:
                        fixed = _ensure_user_char_dataframe(self)
                        if fixed is not self:
                            for col in fixed.columns:
                                if col not in self.columns:
                                    self[col] = fixed[col]
                        elif "user_char" not in self.columns:
                            self["user_char"] = self.apply(_build_user_char_for_row, axis=1)
                except Exception:
                    try:
                        self["user_char"] = "Synthetic fallback agent with neutral behavior and realistic social-media posting habits."
                    except Exception:
                        pass
            return _orig_getitem(self, key)

        pd.read_csv = _patched_read_csv
        pd.DataFrame.__getitem__ = _patched_getitem

        print("[mirofish] v20 user_char runtime guard enabled", flush=True)
    except Exception as exc:
        try:
            print("[mirofish] v20 user_char runtime guard not enabled: %r" % (exc,), flush=True)
        except Exception:
            pass
