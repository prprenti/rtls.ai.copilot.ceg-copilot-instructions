# MC Compilation Debug Reference

## Using grdlbuild

```bash
# Build MC validation code
grdlbuild -p mc -t val

# Build specific target
grdlbuild -p mc -t <target_name>

# Run on netbatch (background)
grdlbuild -p mc -t val -nb
```

## Common Compilation Errors

### Enum Scoping Issues

**Symptom:**
```
Error: Identifier 'ENUM_VALUE' not found
```

**Fix:** Use fully qualified enum names:
```systemverilog
// Bad
state = IDLE;

// Good  
state = state_e::IDLE;
```

### Missing Includes

**Symptom:**
```
Error: Unknown type 'class_name'
```

**Debug:**
```bash
# Find where type is defined
grep -r "class class_name" $WORKAREA/src/val/

# Check include paths in .f file
cat $WORKAREA/src/val/tb/<component>/unit_tests/*_vunit_unittests_inc.f
```

### Package Import Issues

**Symptom:**
```
Error: Identifier 'package_name::symbol' not found
```

**Debug:**
```bash
# Check package definition
grep -r "package package_name" $WORKAREA/src/val/

# Verify import statement exists
grep "import package_name" <failing_file>.sv
```

## Background Job Handling

When running compilation in background:

```bash
# Check if job is still running
jobs -l

# Get netbatch job status
nbqstat -u $USER

# Wait for completion before proceeding
# DO NOT run dependent commands until build completes
```

## Build Order Dependencies

```
1. RTL compile (src/rtl/)
2. Common packages (src/val/common/)
3. TB components (src/val/tb/)
4. Tests (src/val/tests/)
```

Ensure earlier stages complete before compiling dependent code.
