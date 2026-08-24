import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(".github/workflows/scripts/run_ecs_task.sh").resolve()

FAKE_AWS = """#!/usr/bin/env bash
LOG_DIR="$(dirname "$0")"
printf '%s\t' "$@" >> "$LOG_DIR/aws_calls.log"
printf '\n' >> "$LOG_DIR/aws_calls.log"
case "$1 $2" in
  "ecs run-task")
    echo '{"tasks": [{"taskArn": "arn:aws:ecs:test:task/abc"}]}'
    ;;
  "ecs wait")
    ;;
  "ecs describe-tasks")
    echo "$(cat "$LOG_DIR/describe_response.json")"
    ;;
esac
"""


class RunEcsTaskScriptTestCase(unittest.TestCase):
    def run_script(self, args: list[str], describe_tasks_response: str) -> tuple:
        bin_dir = tempfile.mkdtemp()
        fake_aws = Path(bin_dir) / "aws"
        fake_aws.write_text(FAKE_AWS)
        fake_aws.chmod(fake_aws.stat().st_mode | stat.S_IEXEC)
        (Path(bin_dir) / "describe_response.json").write_text(describe_tasks_response)

        env = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "ECS_CLUSTER": "test-cluster",
            "ECS_MIGRATION_TASK_DEFINITION": "test-migration-task",
            "ECS_MIGRATION_SUBNET_ID_LIST": "subnet-1",
            "ECS_MIGRATION_SECURITY_GROUP_LIST": "sg-1",
            "AWS_REGION": "eu-west-2",
        }
        result = subprocess.run(
            [str(SCRIPT), *args], capture_output=True, text=True, env=env
        )
        calls = (Path(bin_dir) / "aws_calls.log").read_text()
        return result, calls

    def test_no_argument_runs_task_without_overrides(self):
        result, calls = self.run_script(
            [], '{"tasks": [{"containers": [{"exitCode": 0}]}]}'
        )

        self.assertEqual(result.returncode, 0)
        self.assertNotIn(
            "--overrides",
            calls,
            "the migration default must run untouched when no command is given",
        )

    def test_argument_overrides_container_command(self):
        result, calls = self.run_script(
            ["python manage.py seed_browser_test_la"],
            '{"tasks": [{"containers": [{"exitCode": 0}]}]}',
        )

        self.assertEqual(result.returncode, 0)
        run_task_args = next(
            line for line in calls.splitlines() if "run-task" in line
        ).split("\t")
        overrides = json.loads(run_task_args[run_task_args.index("--overrides") + 1])
        self.assertEqual(
            overrides["containerOverrides"],
            [
                {
                    "name": "hfu-webapp-ecs-migration",
                    "command": ["-c", "python manage.py seed_browser_test_la"],
                }
            ],
        )

    def test_container_failure_propagates_exit_code(self):
        result, _ = self.run_script(
            [], '{"tasks": [{"containers": [{"exitCode": 3}]}]}'
        )

        self.assertEqual(
            result.returncode,
            3,
            "a failed container must fail the workflow step with its exit code",
        )

    def test_missing_exit_code_fails(self):
        result, _ = self.run_script([], '{"tasks": [{"containers": [{}]}]}')

        self.assertEqual(
            result.returncode,
            1,
            "an unknown outcome must fail rather than pass silently",
        )
