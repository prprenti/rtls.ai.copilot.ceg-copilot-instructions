# Grdlbuild Command Reference

Use this reference after activating the main skill.
Examples are argument templates for the `run_grdlbuild(task, extra_args)` MCP call.

## Listing Tasks

```bash
grdlbuild -st all
grdlbuild -std all
grdlbuild -stfd all
grdlbuild -print_task_tree all
```

Filter listings:

```bash
grdlbuild -st all -dut hubs
grdlbuild -st all -run_modes turnin
grdlbuild -st all -l <label_name>
```

## Running Tasks

Run a single task:

```bash
grdlbuild <task_name> -local
```

Run only the task (ignore deps):

```bash
grdlbuild <task_name> -id -local
```

Run only dependencies:

```bash
grdlbuild <task_name> -run_deps -local
```

Run starting from task:

```bash
grdlbuild <task_name> -sft -local
```

Run after task:

```bash
grdlbuild <task_name> -sat -local
```

Run to endpoint:

```bash
grdlbuild <starting_tasks> -end_at_task <task_name> -local
```

## Scope and Filtering

By DUT:

```bash
grdlbuild all -dut hubs -local
grdlbuild all -dut hubbx -local
```

By run mode:

```bash
grdlbuild all -run_modes turnin -local
grdlbuild all -run_modes mock -local
grdlbuild all -run_modes filter -local
grdlbuild all -run_modes release -local
grdlbuild all -run_modes drop -local
```

By label:

```bash
grdlbuild all -l <label> -local
grdlbuild all -xlabel <label> -local
```

Combined filter:

```bash
grdlbuild all -dut hubs -run_modes turnin -local
```

## Netbatch

Non-blocking:

```bash
grdlbuild <tasks> -nb
grdlbuild all -dut hubs -nb
```

Blocking:

```bash
grdlbuild <tasks> -nb -block
grdlbuild all -dut hubs -nb -block
```

Generate task files only:

```bash
grdlbuild <tasks> -nb_gen
```

Resource class:

```bash
grdlbuild <tasks> -nb -nb_type <section_name>
```

Submission args:

```bash
grdlbuild <tasks> -nb -submission_args "<args>"
```

## Advanced Flags

```bash
grdlbuild <tasks> -disable_gcache -local
grdlbuild <tasks> -disable_tasks_timeout -local
grdlbuild <tasks> -prediction_disable -local
grdlbuild <tasks> -conditionalsOn -local
grdlbuild <tasks> -print_cmd
grdlbuild <tasks> -silent -local
grdlbuild <tasks> -no_log_file -local
```

## Common Task Forms

Task names can use Gradle path notation:

- `:common:create_list_files`
- `:hubs:static:sgdft:sgdft_compile`
- `:hubbx:handoff:h2b:h2b_fullchipdump`
