# Connection & session - deep dive

The curated topics show the *minimum*. Here is more of what you can do once a
session is open. Every fenced block below is runnable - press **Run** on it.

## 1. Explicit client, no helper

`connect()` is convenient but hides the parameters. Build the client yourself
when you want to see (or change) every one of them.

```python
from elo_playground import EloClient, EloError
import os

elo = EloClient(
    base_url=os.environ.get("ELOPG_ELO_BASE_URL", "http://localhost:9090/ix-Repository1"),
    user=os.environ.get("ELOPG_ELO_USER", "Administrator"),
    password=os.environ.get("ELOPG_ELO_PASSWORD", ""),
    verify=False,          # ELO's internal HTTPS is normally self-signed
    timeout=10.0,
)
try:
    user = elo.login()
    print("session for:", user["name"])
    print("server     :", elo.call("getServerInfo", {})["version"])
except EloError as exc:
    # the explicit form always talks to a REAL ELO - in Mock mode there is
    # nothing to log into (the mock only wires up through connect()).
    print("explicit EloClient needs a reachable ELO:", exc)
finally:
    elo.close()
```

> Note: this explicit form talks to a real ELO. In **Mock mode** use
> `connect(login=False)` instead - the mock only wires up through `connect()`.

## 2. One session, many calls

The client keeps the connection (and the session cookie) alive, so chaining
calls is cheap.

```js
import { connect } from "elo-playground";

const elo = await connect();

const info = await elo.call("getServerInfo", {});
const opts = await elo.call("getSessionOptions", {});
const me = elo.user;

console.log(`I am ${me.name} on ${info.instanceName} (IX ${info.version})`);
console.log(`${(opts.options || []).length} session options are set`);
```

## 3. Handling an error envelope

IX reports a *handled* error with `{"exception": ...}` and HTTP 200. The shared
client turns that into an `EloError`.

```python
from elo_playground import connect, EloError

elo = connect()

try:
    # a deliberately bad object id
    elo.call("checkoutSord", {"objId": "999999999", "sordZ": {"bset": "0"}})
except EloError as exc:
    print("caught as expected:", exc)
```

```json
// mock for block 3 - add to this category if you want it to succeed offline:
// "checkoutSord": { "exception": "objectNotFound: 999999999" }
```
