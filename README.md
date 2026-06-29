[![CI](https://github.com/stefanfluit/kirby/actions/workflows/ci.yml/badge.svg)](https://github.com/stefanfluit/kirby/actions/workflows/ci.yml)

# Kirby

![Greeting](http://i.imgur.com/0QkGgYC.png)

Code Coverage Tool for Ansible

## Description

It is usual to measure the code coverage for your source code written in python, Java, and so on. On the other hand, we usually do not measure the coverage for an Ansible playbook. Kirby is the tool to support this.

Here is the example. This is the playbook to be tested. There are 2 tasks.

```yaml
---
- hosts: localhost
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

Here is the [Serverspec](http://serverspec.org/) test. There is 1 test for the first task (create dir1).

```ruby
require 'spec_helper'

describe file('./dir1') do
  it { should be_directory }
end
```

Now, run the playbook. Kirby shows you the code coverage.

```
PLAY [localhost] *************************************************************

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

It tells us the coverage (50%) and the task not tested (Create dir2).

## Requirements

- Python 3.9+
- ansible-core 2.15 or newer
- Ruby + Serverspec (for running the specs)

## Installation

### Option 1: pip + callback plugin file

Install the package:

```
pip install kirby
```

Add the callback plugin to your playbook directory:

```
mkdir callback_plugins
cp callback_plugins/kirby.py /path/to/your/playbook/callback_plugins/
```

Or copy `callback_plugins/kirby.py` from this repository directly.

### Option 2: Ansible Collection

```
ansible-galaxy collection install stefanfluit.kirby
pip install kirby
```

The collection places the callback plugin into your Ansible collection path automatically. You still need `pip install kirby` for the Python package.

### Setup

Create a `kirby.cfg` file in your playbook directory:

```ini
[defaults]
enable = yes

serverspec_dir = ./
serverspec_cmd = bundle exec rake spec
```

* `serverspec_dir` is the directory where Serverspec runs.
* `serverspec_cmd` is the command to invoke Serverspec.

## Usage

### Run

Run `ansible-playbook` as usual.

* Hint: For the best results, your target system should be clean — a playbook has not been executed against it yet.

### Check Results

```
PLAY [localhost] *************************************************************

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

* When a task's result is `changed`, Kirby determines whether the task is tested, and shows you the result.
    * If the line after `tested by:` is empty, the task was not tested (`Create dir2`).
    * If not empty, the task was tested (`Create dir1`).

* When a task's result is not `changed`, Kirby removes the task from the coverage.

* At last, Kirby shows you a summary: the coverage and the list of not tested tasks.

### Improve Coverage

If a task is not tested, write a Serverspec test for it.

However, some tasks may not need tests, such as:

* running `ls` with the `command` module
* downloading a package in preparation for install

There are 2 options:

1. Use `changed_when`

    If a task does not change the target system, use [changed_when](http://docs.ansible.com/ansible/playbooks_error_handling.html#overriding-the-changed-result):

    ```yaml
    - name: List files
      ansible.builtin.command: ls
      changed_when: false
    ```

    Kirby skips tasks whose result is not `changed`.

2. Use `coverage_skip`

    Include `coverage_skip` in the task name:

    ```yaml
    - name: Create workspace [coverage_skip]
      ansible.builtin.file:
        path: ./workspace
        state: directory
    ```

    Kirby skips tasks whose name contains `coverage_skip`.

## Try the Example

The `examples/` directory contains a working demo showing 50% coverage:

```
cd examples
bundle install
ansible-playbook create_files.yml -i inventory
```

## FAQ

* [How does Kirby calculate a coverage?](FAQ.md#work)
* [It takes longer time to run a playbook.](FAQ.md#slow)
* [How can I disable Kirby?](FAQ.md#disable)

## Contributing

Contributions are very welcome, including bug reports, idea sharing, feature requests, and English correction of documents. Feel free to open an issue or a pull request.
