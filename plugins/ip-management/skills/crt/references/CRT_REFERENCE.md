# CRT Reference

## Tool Types

### Types with mandatory Git repositories

| Type | Description | Release Path |
|---|---|---|
| `cheetah_unlocked` | Intel internal tools in Cheetah `$PROJ_TOOLS` | `/p/cth/pu_tu/prd/<tool>/<version>` |
| `hdk_proj_tools` | Intel internal tools in HDK `$PROJ_TOOLS` | `/p/hdk/pu_tu/prd/<tool>/<version>` |
| `proj_cfg` | Project config data in `PROJ_CFG` | `/p/hdk/cfg/data/<tool>/<version>` |

### Types without mandatory Git repositories

| Type | Description | Release Path |
|---|---|---|
| `cheetah_cad` | Intel CAD tools in Cheetah `$CAD_ROOT` | `/p/cth/cad/<tool>/<version>` |
| `hdk_cad` | Intel CAD tools in HDK `$CAD_ROOT` | `/p/hdk/cad/<tool>/<version>` |
| `rtl_cad` | Front-end vendor tools in `$RTL_CAD_ROOT` | `/p/hdk/rtl/cad/x86-64_linux26/<tool>/<version>` |
| `rtl_proj_tools` | Intel front-end internal tools in `$RTL_PROJ_TOOLS` | `/p/hdk/rtl/proj_tools/<tool>/<version>` |
| `sde` | DSLC tools in SDE area | `/nfs/site/proj/dt/sde/tools/commonOS/<tool>/<version>` |
| `proj_lib_dbin` | Front-end contour | `/p/hdk/rtl/proj_[dbin/lib]/<project>` → `.../latest` |

> **`proj_lib_dbin` note:** Always include `-updatelink latest`. File a
> ticket at http://goto.intel.com/pds_support for link setup.

### Other types

| Type | Area |
|---|---|
| `bin` | General binary tools |
| `cheetah_flow` | Cheetah flow tools |
| `dt_cad` | DT CAD tools |
| `dt_tools` | DT tools |
| `hs_cad` | HS CAD tools |
| `hs_proj_tools` | HS project tools |

### Reverse lookup: Unix path → tool type

| Path prefix | Tool type |
|---|---|
| `/p/cth/pu_tu/prd/` | `cheetah_unlocked` |
| `/p/cth/cad/` | `cheetah_cad` |
| `/p/hdk/pu_tu/prd/` | `hdk_proj_tools` |
| `/p/hdk/cad/` | `hdk_cad` |
| `/p/hdk/cfg/data/` | `proj_cfg` |
| `/p/hdk/rtl/cad/x86-64_linux26/` | `rtl_cad` |
| `/p/hdk/rtl/proj_tools/` | `rtl_proj_tools` |
| `/p/hdk/rtl/proj_dbin/` or `/p/hdk/rtl/proj_lib/` | `proj_lib_dbin` |
| `/nfs/site/proj/dt/sde/tools/commonOS/` | `sde` |

### Tool Classifications

Used with `-class`: `confidential`, `topsecret`, `hasupf`

---

## Actions Reference

### 1. Register New Tool

#### `crt register`

```
crt register -tool <name> -type <type> -class <classification> \
  [-sites <s1,s2>] [-repo <ssh-url> | -createrepo] [-desc <description>] \
  [-quota <version-quota>] [-maintainer <user1,user2>] \
  [-includedotgitinrelease] [-allowbrokenlinks <0/1>] \
  [-repotomigratefrom <repo>] [-defaultbranch <master|main>] \
  [-repotype <Type-#>] [-repotypedesc "<description>"]
```

- `-tool` — Tool name (required)
- `-type` — Tool type (required)
- `-class` — Security classification (required)
- `-sites` — Default installation sites
- `-repo` — SSH URL of the tool's repository
- `-createrepo` — Create a new repo with master branch
- `-desc` — Short description
- `-quota` — Max versions allowed
- `-maintainer` — Maintainer list
- `-defaultbranch` — Default branch: `master` or `main`
- `-defaultgroup` — Default release group

#### `crt approve`

```
crt approve -tool <name> [-type <type>]
```

Required before first release.

#### `crt retire`

```
crt retire -tool <name> [-type <type>]
```

---

### 2. Version Management

#### `crt install`

```
crt install -tool <name> [-type <type>] [-src <source-dir>] \
  [-version <version>] [-group <group>] [-sites <s1,s2>] \
  [-updatelink <link-name>] [-replace] [-partial <path>] \
  [-releaseFromTag <tag>] [-patch] [-project <project>] \
  [-dryrun] [-versionComment "<comment>"] \
  [-onduplication <fail|link>] [-allowbrokenlinks <0/1>] \
  [-excludeSubmodules] [-includedotgitinrelease] \
  [-customGroup [-configFilePath <path>] [-enforceCustomGroup]] \
  [-imageFilePath <path>] [-harborGroup <group>] [-harborSites <s1,s2>] \
  [-pathToSaveSIF <path>] [-moveToNewDisk] [-retainReleaseSites]
```

Key switches:
- `-tool` — Tool name (required)
- `-src` — Source directory (default: current dir)
- `-version` — Explicit version (default: auto-calculated)
- `-group` — Release group (default: registered default or `soc`)
- `-sites` — Release sites
- `-updatelink` — Create/update link to this version
- `-replace` — Reinstall existing non-production version
- `-releaseFromTag <tag>` — Release from Git tag
- `-patch` — Patch release
- `-dryrun` — Simulate without changes
- `-onduplication fail|link` — Duplicate behavior

#### `crt rmVersion`

```
crt rmVersion -tool <name> -version <v1,v2> [-sites <s1,s2>] [-type <type>]
```

#### `crt link`

```
crt link -tool <name> -linkname <link> -linkto <version> \
  [-type <type>] [-force] \
  [-target tool=<name>] [-target version=<ver>] [-target type=<type>]
```

#### `crt rmLink`

```
crt rmLink -tool <name> -linkname <link> [-type <type>]
```

#### `crt replicate`

```
crt replicate -tool <name> -version <v1,v2> -sites <s1,s2> \
  [-type <type>] [-dryrun] [-toolList <file>]
```

#### `crt rename`

```
crt rename -tool <name> -currentversion <old> -newversion <new> [-type <type>]
```

#### `crt lock / unlock`

```
crt lock   -tool <name> [-version <v1,v2,v3>] [-comment "<text>"] [-lockTool] [-type <type>]
crt unlock -tool <name> [-version <v1,v2,v3>] [-unlockTool] [-type <type>]
```

- `-lockTool` / `-unlockTool` — Lock/unlock entire tool
- `-version` — Lock/unlock specific versions

#### `crt status`

```
crt status -tool <name> -version <version> [-type <type>] \
  [-sites <s1,s2>] [-details] [-toolList <file>]
```

#### `crt showNextVersion`

```
crt showNextVersion -tool <name> [-type <type>] [-src <path>] [-beta] [-patch]
```

#### `crt listReleasedVersions`

```
crt listReleasedVersions -tool <name> [-type <type>]
```

#### `crt getVersionInfo`

```
crt getVersionInfo -tool <name> -version <version> [-type <type>]
```

#### `crt updateVersionComment`

```
crt updateVersionComment -tool <name> -version <version> \
  -versionComment "<comment>" [-type <type>]
```

#### `crt checkVersionsActivity`

```
crt checkVersionsActivity -tool <name> \
  -version <v1,v2|all> -inactiveLongerThan <6M|1Y|2Y|5Y|10Y> \
  -numOfVersionsToCheck <N> [-type <type>] [-details] \
  [-sites <s1,s2>] [-format csv] \
  [-generateRemoveCommandPerVersion] \
  [-filesToCheck <file1,file2>] [--timeout <seconds>]
```

---

### 3. Sandbox Management

#### `crt mkSbox`

```
crt mkSbox -tool <name> -target <work-area-path> \
  [-type <type>] [-name <sandbox-name>] \
  [-integrationBranch <branch>] [-force]
```

#### `crt rmSbox`

```
crt rmSbox -tool <name> [-type <type>] [-name <sandbox-name>]
```

---

### 4. Extract Tool Information

#### `crt showTools`

```
crt showTools [-mine | -all] [-format <table|json>] [-sortby <registration|name>]
```

> `-mine` may take up to 20 min; use `crt showTools | grep <IDSID>` instead.

#### `crt getToolInfo`

```
crt getToolInfo -tool <name> [-type <type>]
```

#### Simple Queries

All take `-tool <name> [-type <type>]`:
- `crt getDesc`
- `crt getDefaultGroup`
- `crt getRegSites`
- `crt getRepo`
- `crt getVersionQuota`
- `crt getClass`

---

### 5. Update Tool Information

#### `crt updateToolInfo`

```
crt updateToolInfo -tool <name> [-type <type>] \
  [-sites <s1,s2>] [-desc <description>] [-quota <N>] \
  [-defaultgroup <group>] [-class <classification>] \
  [-repo <url> | -createrepo] [-removerepo] \
  [-includedotgitinrelease <0|1>] [-allowbrokenlinks <0|1>] \
  [-defaultbranch <master|main>] [-releasetoconstantdisk <0|1>] \
  [-includepreinstallinrelease <0|1>]
```

---

### 6. Access Management

#### `crt addAccess / rmAccess`

```
crt addAccess -tool <name> [-type <type>] [-branch <branch>] \
  [-maintainer <user1,user2>] [-owners <user1,user2>] \
  [-contributors <user1,user2>] [-readonly <user1,user2>] \
  [-notifyonrelease <user1,user2>]
```

Access roles:

| Role | Permissions |
|---|---|
| **maintainer** | Release/delete versions; manage maintainers |
| **owner** | Edit repository; manage owners, contributors, readonly |
| **contributor** | Edit repository |
| **readonly** | Clone only (intel-restricted repos) |
| **notifyonrelease** | Notification on new releases |

#### `crt getAccess`

```
crt getAccess -tool <name> [-type <type>] [-branch <branch>] [-show_admins]
```

---

### 7. Git Operations

#### `crt clone`

```
crt clone -tool <name> -target <path> [-type <type>] \
  [-integrationBranch <branch>] [-excludeSubmodules]
```

#### `crt establish`

```
crt establish [-integrationBranch <branch>] [-validate] [-excludeSubmodules]
```

Run inside cloned repo directory.

#### `crt update`

```
crt update [-submodules] [-excludeSubmodules]
```

#### `crt repoStatus`

```
crt repoStatus [-short]
```

#### `crt mkbranch`

```
crt mkbranch -tool <name> \
  {-patch <version> | -project <name> | -feature <name> | -custom <name>} \
  [-type <type>] [-owners <user1,user2>]
```

Branch naming conventions:

| Switch | Convention | Purpose |
|---|---|---|
| `-patch <version>` | `P_<version>` | Patch branch |
| `-project <name>` | `D_<name>` | Project branch |
| `-feature <name>` | `F_<name>` | Feature branch |
| `-custom <name>` | `<name>` | Custom name |

#### `crt protectBranch`

```
crt protectBranch -tool <name> -branch <branch> [-type <type>] [-owners <user1,user2>]
```

---

### 8. Container Management (Harbor / Singularity)

#### `crt createSingularityImageFile`

```
crt createSingularityImageFile \
  -definitionFilePath <path-to-def> -pathToSaveSIF <path> \
  [-tool <name>] [-type <type>] [-version <version>] \
  [-upload] [-harborGroup <group>] [-harborSites <s1,s2>] \
  [-replace] [-replaceImage] [-defFile <files>]
```

#### `crt uploadImageToHarbor`

```
crt uploadImageToHarbor -tool <name> -version <version> \
  -imageFilePath <path-to-sif> [-type <type>] \
  [-harborGroup <group>] [-harborSites <s1,s2>] [-replace]
```

#### `crt downloadImageFromHarbor`

```
crt downloadImageFromHarbor -tool <name> -version <version> \
  [-type <type>] [-pathToSaveSIF <path>]
```

#### `crt deleteImageFromHarbor`

```
crt deleteImageFromHarbor -tool <name> -version <version> \
  [-type <type>] [-harborGroup <group>] [-harborSites <s1,s2>]
```

---

### 9. CRT Agent

```
crt agent [-web] [-cli]
```

Interactive AI helper for CRT questions. Defaults to web mode.
