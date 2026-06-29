import os
import re
import subprocess
import time

from behave import given, then, when


@given("the target host is clean")
def step_impl(context):  # noqa: F811
    for env_var in ["KIRBY_CONFIG", "KIRBY_ENABLE"]:
        if env_var in os.environ:
            del os.environ[env_var]

    for f in os.listdir("."):
        if re.search(r"^dummy.*\.conf$", f):
            os.remove(f)


@given('use "{config_file}" as a config file')
def step_impl(context, config_file):  # noqa: F811
    os.environ["KIRBY_CONFIG"] = config_file


@given("env var is used instead of config file")
def step_impl(context):  # noqa: F811
    os.environ["KIRBY_ENABLE"] = "yes"
    os.environ["KIRBY_SERVERSPEC_DIR"] = "./"
    os.environ["KIRBY_SERVERSPEC_CMD"] = "bundle exec rake spec"


@given("kirby is disabled")
def step_impl(context):  # noqa: F811
    os.environ["KIRBY_ENABLE"] = "no"


@when('we run the playbook "{playbook}"')
def step_impl(context, playbook):  # noqa: F811
    cmd = f"ansible-playbook {playbook} -i inventory"

    start = time.time()
    try:
        context.cmd_output = subprocess.check_output(
            cmd, shell=True, stderr=subprocess.STDOUT
        ).decode("utf-8", errors="replace")
        context.cmd_rc = 0
    except subprocess.CalledProcessError as ex:
        context.cmd_output = ex.output.decode("utf-8", errors="replace")
        context.cmd_rc = ex.returncode
    context.elapsed = time.time() - start


@then('stdout will include "{coverage}" as a coverage')
def step_impl(context, coverage):  # noqa: F811
    assert f" {coverage} " in context.cmd_output


@then('stdout will not include "{coverage}" as a coverage')
def step_impl(context, coverage):  # noqa: F811
    assert f" {coverage} " not in context.cmd_output


@then('stdout will not include "{warning}"')
def step_impl(context, warning):  # noqa: F811
    assert warning not in context.cmd_output


@then('stdout will include "{warning}"')
def step_impl(context, warning):  # noqa: F811
    assert warning in context.cmd_output


@then('elapsed time will be less than "{max_time}" seconds')
def step_impl(context, max_time):  # noqa: F811
    assert context.elapsed < float(max_time)
