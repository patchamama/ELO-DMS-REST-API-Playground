"""Dev tool: capture read-only IX responses from a sample ELO into ``fixtures/ix/swagger.json``.

    runtime/python-venv/Scripts/python.exe scripts/capture_swagger_mock.py \
        http://localhost:9090/ix-Contelo Administrator elo

The file feeds the Swagger tab's "Try it out" in mock mode (local app and the
static GitHub Pages demo). Only read-only methods are called. Run it against a
sample repository only - the output is committed verbatim.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared" / "python"))

from elo_playground import EloError, connect  # noqa: E402

OUT = ROOT / "fixtures" / "ix" / "swagger.json"
ALL = "449304431574384639"  # "every Sord field" bitset


def main(base_url: str, user: str, password: str) -> int:
    elo = connect(base_url=base_url, user=user, password=password)
    out: dict = {"_comment": "Captured from a sample ELO 25 repository by scripts/capture_swagger_mock.py. Read-only calls only."}

    def grab(method: str, body: dict, *, key: str | None = None, trim=None) -> object:
        try:
            res = elo.call(method, body)
        except EloError as exc:
            print(f"  skip {method}: {str(exc)[:110]}")
            return None
        if trim:
            trim(res)
        out.setdefault(key or method, res)
        print(f"  ok   {key or method}")
        return res

    def cap(field: str, n: int):
        def _t(res):
            if isinstance(res, dict) and isinstance(res.get(field), list):
                res[field] = res[field][:n]
        return _t

    grab("getServerInfo", {})
    grab("getSessionOptions", {})
    grab("getServerInfoDM", {})
    grab("checkoutSord", {"objId": "1", "editInfoZ": {"bset": "1", "sordZ": {"bset": ALL}}})
    grab("checkoutSordTypes", {"sordTypesZ": {"bset": "1"}}, trim=cap("sordTypes", 8))
    first = grab("findFirstSords", {"findInfo": {"findChildren": {"parentId": "1", "mainParent": False, "endLevel": 1}}, "max": 5, "sordZ": {"bset": ALL}}, trim=cap("sords", 5))
    if isinstance(first, dict) and first.get("searchId") is not None:
        grab("findNextSords", {"searchId": first["searchId"], "idx": 5, "max": 5, "sordZ": {"bset": ALL}}, trim=cap("sords", 5))
        try:
            elo.call("findClose", {"searchId": first["searchId"]})
        except EloError:
            pass
    users = grab("findFirstUsers", {"findUserInfo": {"type": 0}, "max": 8}, trim=cap("users", 8))
    if isinstance(users, dict) and users.get("searchId") is not None:
        try:
            elo.call("findClose", {"searchId": users["searchId"]})
        except EloError:
            pass
    grab("checkoutUsers", {"ids": [0], "checkoutUsersZ": {"bset": "513"}})
    grab("checkoutDocMask", {"maskId": "0", "docMaskZ": {"bset": "1"}, "lockZ": {"bset": "0"}})
    grab("checkoutKeywordList", {"kwid": "ELOSTDSWL", "max": 20, "keywordZ": {"bset": "7"}})
    wf = grab("findFirstWorkflows", {"findInfo": {"type": {"bset": "2"}, "inclHidden": True}, "max": 5, "wfDiagramZ": {"bset": "0"}}, trim=cap("workflows", 5))
    if isinstance(wf, dict) and wf.get("searchId") is not None:
        try:
            elo.call("findClose", {"searchId": wf["searchId"]})
        except EloError:
            pass

    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(out) - 1} methods, {OUT.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(*sys.argv[1:]))
