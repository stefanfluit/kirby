# Kirby Example

This example runs a two-task Ansible playbook and shows Kirby measuring coverage.

**What it does:**

- Creates `/tmp/kirby-example/hello.txt` — has a Serverspec test → **tested**
- Creates `/tmp/kirby-example/world.txt` — no Serverspec test → **not tested**

**Expected output:**

```
*** Kirby Results ***
Coverage  : 50% (1 of 2 tasks are tested)
Not tested:
 - Create world.txt
*** Kirby End *******
```

## Prerequisites

Install the kirby package (from the project root):

```
pip install -e ..
pip install ansible-core
```

Install Ruby dependencies:

```
bundle install
```

## Run

```
ansible-playbook create_files.yml -i inventory
```

The playbook resets `/tmp/kirby-example` at the start, so it produces the same result on every run.

## How it works

1. **Before the playbook** — Kirby runs Serverspec as a baseline. `hello.txt` does not exist yet, so the spec fails (1 failure).
2. **After `create hello.txt`** — Kirby runs Serverspec again. The spec now passes (0 failures). Failures decreased → task is **tested**.
3. **After `create world.txt`** — Kirby runs Serverspec again. Still 0 failures (no spec for `world.txt`). Failures did not decrease → task is **not tested**.

The two prep tasks use `[coverage_skip]` in their names, so Kirby skips them entirely.

## Cleanup

```
rm -rf /tmp/kirby-example
```
