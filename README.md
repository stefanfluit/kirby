[![CI](https://github.com/stefanfluit/kirby/actions/workflows/ci.yml/badge.svg)](https://github.com/stefanfluit/kirby/actions/workflows/ci.yml)

# Kirby

![Greeting](http://i.imgur.com/0QkGgYC.png)

Ansible task coverage via Serverspec.

## Description

Kirby is a callback plugin that measures which of your changed Ansible tasks are covered by Serverspec tests. After each task that reports `changed`, Kirby re-runs your spec suite and attributes any newly passing tests to that task. At the end of the play it prints a coverage summary — percentage, tested tasks, and gaps.

## Example

```yaml
---
- name: Demo
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Create dir1
      ansible.builtin.file:
        path: ./dir1
        state: directory

    - name: Create dir2
      ansible.builtin.file:
        path: ./dir2
        state: directory
```

One Serverspec test covers the first task:

```ruby
require 'spec_helper'

describe file('./dir1') do
  it { should be_directory }
end
```

Running the playbook with Kirby active:

```
TASK [Create dir1] ***********************************************************
changed: [localhost]
tested by:
- rspec ./spec/localhost/sample_spec.rb:4 # File "./dir1" should be directory

TASK [Create dir2] ***********************************************************
changed: [localhost]
tested by:

PLAY RECAP *******************************************************************
*** Kirby Results ***
Coverage  : 50% (1 of 2 tasks are tested)
Not tested:
 - Create dir2
*** Kirby End *******
```

## Requirements

- Python 3.9+
- ansible-core 2.15.0 or newer
- Ruby + Serverspec

## Installation

```shell
ansible-galaxy collection install stefanfluit.kirby
```

The collection includes both the callback plugin and its Python runtime — nothing else to install.

### Configuration

Create a `kirby.cfg` in your playbook directory:

```ini
[defaults]
enable = yes

serverspec_dir = ./
serverspec_cmd = bundle exec rake spec
```

| Key | Description |
| --- | --- |
| `serverspec_dir` | Directory from which Serverspec is invoked |
| `serverspec_cmd` | Command used to run Serverspec |

## Usage

Run `ansible-playbook` as normal. For accurate results, run against a clean target that hasn't had the playbook applied yet.

After each `changed` task, Kirby shows which spec examples newly passed — those are attributed as covering that task. Tasks with no newly passing specs appear in the "Not tested" list.

### Excluding tasks from coverage

Some tasks don't warrant a Serverspec test. Two ways to exclude them:

**`changed_when: false`** — for tasks that don't meaningfully modify the target:

```yaml
- name: List files
  ansible.builtin.command: ls
  changed_when: false
```

Kirby ignores tasks whose result is not `changed`.

**`coverage_skip`** in the task name — for tasks you explicitly want to skip:

```yaml
- name: Create workspace [coverage_skip]
  ansible.builtin.file:
    path: ./workspace
    state: directory
```

## Try the Example

The `examples/` directory contains a working demo:

```shell
cd examples
bundle install
ansible-playbook create_files.yml -i inventory
```

## FAQ

**How does Kirby calculate coverage?**
After each `changed` task, Kirby re-runs Serverspec and compares the failure count. If failures decreased, the task is considered tested. Coverage = tested tasks / total changed tasks.

**Why does my playbook run slower?**
Kirby invokes Serverspec after every changed task. Use `changed_when: false` on tasks that don't modify state, or tag them with `[coverage_skip]` to reduce the number of Serverspec runs.

**How do I disable Kirby?**
`export KIRBY_ENABLE=no`

## Contributing

Bug reports, feature requests, and pull requests are welcome. Open an issue or PR on GitHub.
