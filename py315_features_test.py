"""Smoke tests for new Python 3.15 features.

Run:  py -3.15 py315_features_test.py
Each test prints PASS / FAIL / SKIP so one missing feature doesn't hide the rest.
"""
import io
import os
import subprocess
import sys
import tempfile
import traceback

results = []


def test(fn):
    name = fn.__name__.removeprefix("test_")
    try:
        outcome = fn()
        status = "SKIP" if outcome == "skip" else "PASS"
    except Exception:
        status = "FAIL"
        traceback.print_exc()
    results.append((name, status))
    print(f"[{status}] {name}")
    return fn


@test
def test_utf8_default_open():
    path = os.path.join(tempfile.gettempdir(), "py315_utf8.txt")
    text = "café ✓ 日本語"
    with open(path, "w") as f:          # no encoding= on purpose
        f.write(text)
    with open(path, "rb") as f:
        assert f.read() == text.encode("utf-8"), "file was not written as UTF-8"
    with open(path) as f:
        assert f.read() == text
    os.remove(path)


@test
def test_lazy_import():
    code = (
        "import sys\n"
        "lazy import json\n"
        "loaded_before = 'json' in sys.modules\n"
        "json.dumps({})\n"
        "loaded_after = 'json' in sys.modules\n"
        "assert not loaded_before, 'json loaded eagerly'\n"
        "assert loaded_after\n"
    )
    exec(compile(code, "<lazy>", "exec"), {"__name__": "lazy_test"})


@test
def test_unpacking_in_comprehension():
    # Compiled at test time: on builds without this syntax it fails only this test.
    ns = {"nested": [[1, 2], [3], [4, 5]]}
    exec("result = [*sub for sub in nested]", ns)
    assert ns["result"] == [1, 2, 3, 4, 5]


@test
def test_sentinel():
    MISSING = sentinel("MISSING")       # new builtin
    assert MISSING is MISSING
    assert "MISSING" in repr(MISSING)


@test
def test_frozendict():
    fd = frozendict(a=1, b=2)
    assert fd["a"] == 1
    assert isinstance(hash(fd), int)
    try:
        fd["c"] = 3
    except TypeError:
        pass
    else:
        raise AssertionError("frozendict should be immutable")


@test
def test_counter_symmetric_difference():
    from collections import Counter
    assert Counter(a=3, b=1) ^ Counter(a=1, c=2) == Counter(a=2, c=2, b=1)


@test
def test_re_prefixmatch():
    import re
    assert re.prefixmatch(r"\d+", "123abc").group() == "123"
    assert re.prefixmatch(r"\d+", "abc123") is None


@test
def test_unicodedata_iter_graphemes():
    import unicodedata
    s = "e\u0301🇺🇸👨‍👩‍👧"    # e+accent, flag, family emoji
    parts = list(unicodedata.iter_graphemes(s))
    assert len(parts) == 3, parts


@test
def test_pprint_expand():
    import pprint
    # expand only affects structures that don't fit on one line, so force a break.
    data = {"a": [1, 2, 3], "b": {"c": 4}}
    plain = pprint.pformat(data, width=20)
    expanded = pprint.pformat(data, width=20, expand=True, indent=3)
    print("   plain:   ", repr(plain))
    print("   expanded:", repr(expanded))
    assert expanded != plain, "expand=True changed nothing"
    assert expanded.startswith("{\n"), "expected JSON-style newline after opening brace"


@test
def test_better_error_message():
    try:
        [].push(1)
    except AttributeError as e:
        # Suggestion is added when the traceback is formatted.
        text = "".join(traceback.format_exception(e))
        assert "append" in text, text
    else:
        raise AssertionError("expected AttributeError")


@test
def test_sampling_profiler_available():
    r = subprocess.run([sys.executable, "-m", "profiling.sampling", "--help"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


print("\nPython", sys.version)
failed = [n for n, s in results if s == "FAIL"]
print(f"{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
