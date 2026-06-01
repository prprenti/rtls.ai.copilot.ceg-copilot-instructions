# HSD CLI & API Reference

Background reference for HSD operations. The MCP tools (`hsd_query`, `hsd_get_article`,
`hsd_field_info`, `hsd_update_article`, `hsd_add_comment`, `hsd_clone_article`,
`get_hsd_release`) handle all routine workflows — use the MCP tools directly rather
than running the CLI tools below.

The CLI and REST API sections here document what the MCP tools invoke internally,
and provide syntax for scripting or automation that falls outside the MCP tool scope.

---

## EQL Syntax Reference

EQL is the query language passed to `hsd/hsd_query(eql=...)`.

```sql
SELECT id,title,status,owner
WHERE subject='feature' AND family='TITAN LAKE'
  AND status NOT IN ('rejected', 'future')
SORTBY submitted_date DESC
```

**Operators:** `=`, `!=`, `IN`, `NOT IN`, `CONTAINS`, `STARTS_WITH`, `ENDS_WITH`,
`IS_EMPTY`, `IS_NOT_EMPTY`, `IS ME`, `DaysAgo(N)`, `WeeksAgo(N)`, `Today`

### Scoping Value Examples

| Level | Family | Release | Component |
|-------|--------|---------|-----------|
| IU/IP | CEG IUs | punit-ttl-h-a0 | punit.ip.top.hw |
| Subsystem | CEG Subsystems | subsystem_memss-ttl-h-a0 | subsystem_memss.ip.mc.iu.hw# |
| SOC | Titan Lake HUB-P 4LPE Die | ttl-h-a0 | ttl.soc.ip.punit.iu.hw# |

### Useful Query Patterns

Open/active bugs:
```sql
subject='bugeco' AND status IN ('open', 'approved')
```

Exclude closed:
```sql
subject='bugeco' AND status NOT IN ('complete', 'rejected', 'future', 'repo_modified')
```

Recent articles:
```sql
subject='bugeco' AND submitted_date > DaysAgo(30)
```

Cloned from a specific article (use `from_id`, not `lineage`):
```sql
subject='bugeco' AND from_id=<source_id>
```

IU-level bugs (family is always `CEG IUs`):
```sql
subject='bugeco' AND family='CEG IUs' AND release='hbo-ttl-h-a0'
```

### Default Display Fields

Pass to `hsd/hsd_query(fields=...)`:
```
family,release,component,id,title,status,owner
```

---

## Field Metadata (via MCP)

Use `hsd/hsd_field_info` to validate field values before writing:

```
hsd/hsd_field_info(subject="bugeco")                   # list all fields
hsd/hsd_field_info(subject="bugeco", field="release")  # allowed values for release
hsd/hsd_field_info(subject="bugeco", field="family")   # allowed values for family
```

Always call this before `hsd_update_article` or `hsd_clone_article` when you are not
certain a `family`, `release`, or `component` value exists.

---

## CLI Tools (Background Reference)

Tools are at `/p/cth/rtl/proj_tools/hsdes/linux-tools/prod/`.
These are what the MCP server calls internally. Do not invoke them directly through Copilot.

### esinfo — field metadata

```bash
esinfo <tenant>                               # list subjects
esinfo <tenant>.<subject>                     # list fields
esinfo <tenant>.<subject>.<field>             # allowed values
esinfo -article <article_id>                  # fields of a specific article
esinfo -magazine "<mag>" -savedquery "<q>"    # get EQL for a saved query
```

### esquery — read/search

```bash
esquery <article_id>
esquery -where "subject='bugeco' AND ..." -show id,title,status -csv
esquery -magazine "<mag>" -savedquery "<q>"
esquery -subject bugeco -iown
esquery -where "..." -mailme -mailsubject "Results" -html
```

### esupdate — write (preview-first in MCP)

```bash
esupdate <id> status=resolved owner=$USER
esupdate <id> tag+=NEW_TAG
esupdate <id> -comment "text"
esupdate -create heia_soc.bugeco title="..." owner=$USER
esupdate -cloneto heia_soc.bugeco <source_id> release=new-release
```

The MCP enforces `confirm=False` (dry-run) by default for all write operations.

---

## REST API

### Authentication

Kerberos (preferred for interactive use):

```python
from requests_kerberos import HTTPKerberosAuth
import requests

response = requests.get(
    'https://hsdes-api.intel.com/rest/article/12345678',
    auth=HTTPKerberosAuth()
)
```

API token (for unattended scripts):

```python
from requests.auth import HTTPBasicAuth
response = requests.get(
    'https://hsdes-api.intel.com/rest/article/12345678',
    auth=HTTPBasicAuth('your_idsid', 'your_token')
)
```

SSL: download Intel CA bundle from [Intel Certificate Trust Chain](https://certificates.intel.com/Trust).
Never use `verify=False` in production.

### Common Endpoints

- `GET /article/{id}` — Fetch article
- `POST /article` — Create article
- `PUT /article/{id}` — Update article
- `POST /article/{id}/clone` — Clone article
- `GET /query/{tenant}/{subject}?query=<EQL>` — EQL query

### Inconsistency: sendmail vs send_mail

- Clone (`POST /article/{id}/clone`): use `sendmail` (no underscore) in body
- Update (`PUT /article/{id}`): use `send_mail` (with underscore) in `fieldValues`
- CLI equivalent: `-nosendmail` flag on `esupdate`

---

## Scripting Patterns

These patterns apply to Python scripts that call HSD directly (outside the MCP).

### EQL Query

```python
def query_via_eql(eql_query, max_results=10000):
    url = f'https://hsdes-api.intel.com/rest/query/execution/eql?start_at=1&max_results={max_results}'
    payload = f'{{"eql":"{eql_query}"}}'
    response = requests.post(url, auth=HTTPKerberosAuth(),
                             headers={'Content-type': 'application/json'}, data=payload)
    response.raise_for_status()
    return response.json().get('data', [])
```

### Update Article Fields

Use `fieldValues` array — flat JSON fails with 400:

```python
# WRONG: flat JSON
payload = {'tenant': 'heia_soc', 'subject': 'task', 'owner': 'newowner'}

# CORRECT: fieldValues wrapper
payload = {
    'tenant': 'heia_soc',
    'subject': 'task',
    'fieldValues': [{'owner': 'newowner', 'send_mail': 'false'}]
}
requests.put(f'https://hsdes-api.intel.com/rest/article/{id}',
             auth=HTTPKerberosAuth(), headers={'Content-type': 'application/json'}, json=payload)
```

### Clone Article

```python
clone_data = {
    'destTenant': 'heia_soc',
    'destSubject': 'bugeco',
    'sendmail': 'false',        # no underscore for clone
    'copy_attachment': 'false',
    'copy_comment': 'false',
    'fieldValues': [{'release': 'new-release'}]
}
requests.post(f'https://hsdes-api.intel.com/rest/article/{source_id}/clone',
              auth=HTTPKerberosAuth(), headers={'Content-type': 'application/json'}, json=clone_data)
```

### Article History

```python
def get_article_history(article_id):
    url = f'https://hsdes-api.intel.com/rest/article/{article_id}/history'
    response = requests.get(url, auth=HTTPKerberosAuth())
    response.raise_for_status()
    data = response.json()
    history = data.get('data', data) if isinstance(data, dict) else data
    return sorted(history, key=lambda x: int(x.get('rev', 0)))
```

### Date Parsing

```python
def parse_hsd_datetime(date_str):
    if not date_str:
        return None
    try:
        if 'T' in date_str:
            date_str = date_str.split('+')[0].split('Z')[0]
            return datetime.fromisoformat(date_str.replace('T', ' ').split('.')[0])
        return datetime.strptime(date_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None
```

### Intel Work-Week Key

```python
def get_iso_week_key(dt):
    iso_year, week, day = dt.isocalendar()
    return f"{iso_year}ww{week:02d}_{day}"
```

---

## Resources

- [HSD-ES Wiki](https://wiki.ith.intel.com/spaces/HSDESWIKI/pages/845189598/HSD-ES+Home)
- [EQL Documentation](https://wiki.ith.intel.com/spaces/HSDESWIKI/pages/989735087/EQL+-+ES+Query+Language)
- [HSD-ES API Docs](https://wiki.ith.intel.com/spaces/HSDESWIKI/pages/954011548/HSD-ES+API)
