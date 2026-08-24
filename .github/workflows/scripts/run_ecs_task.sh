#!/usr/bin/env bash
TASK_COMMAND="${1:-}"
TASK_LABEL="${TASK_COMMAND:-migration}"

RUN_TASK_ARGS=(
    --cluster "$ECS_CLUSTER"
    --launch-type FARGATE
    --task-definition "$ECS_MIGRATION_TASK_DEFINITION"
    --network-configuration "awsvpcConfiguration={subnets=[${ECS_MIGRATION_SUBNET_ID_LIST}],securityGroups=[${ECS_MIGRATION_SECURITY_GROUP_LIST}]}"
)

if [ -n "$TASK_COMMAND" ]; then
    OVERRIDES=$(jq -cn --arg command "$TASK_COMMAND" \
        '{containerOverrides: [{name: "hfu-webapp-ecs-migration", command: ["-c", $command]}]}')
    RUN_TASK_ARGS+=(--overrides "$OVERRIDES")
fi

echo "Starting ECS task: $TASK_LABEL"

RUN_TASK_OUTPUT=$(aws ecs run-task "${RUN_TASK_ARGS[@]}")

TASK_ARN=$(echo "$RUN_TASK_OUTPUT" | jq -r '.tasks[0].taskArn')

echo "Waiting for ECS task to stop"
aws ecs wait tasks-stopped --cluster "$ECS_CLUSTER" --tasks "$TASK_ARN" --region "$AWS_REGION"
echo "ECS task has stopped"

TASK_DETAILS=$(aws ecs describe-tasks --cluster "$ECS_CLUSTER" --tasks "$TASK_ARN" --region "$AWS_REGION")

EXIT_CODE=$(echo "$TASK_DETAILS" | jq -r '.tasks[0].containers[0].exitCode')
if [ -z "${EXIT_CODE:-}" ] || [ "$EXIT_CODE" = "null" ]; then
  echo "EXIT_CODE is empty or unset"
  exit 1
fi

if [ "$EXIT_CODE" -eq 0 ]; then
  echo "ECS task ($TASK_LABEL) succeeded"
else
  echo "ECS task ($TASK_LABEL) failed with code $EXIT_CODE"
  exit "$EXIT_CODE"
fi
