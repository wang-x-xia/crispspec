"""Type constants for crispsec project."""

draft = "draft"
requirement = "requirement"
user_story = "user-story"
business_concept = "business-concept"
entity = "entity"
interface = "interface"
event = "event"
error = "error"
process = "process"
orchestration = "orchestration"
reaction = "reaction"
schedule = "schedule"
repository = "repository"
code_ref = "code-ref"
incident = "incident"
runbook = "runbook"
playbook = "playbook"
constraint = "constraint"
metric = "metric"
role = "role"
permission = "permission"
dependency = "dependency"
module = "module"
environment = "environment"
pipeline = "pipeline"
configuration = "configuration"
config_set = "config-set"
confidential = "confidential"
acceptance_test = "acceptance-test"
scenario_test = "scenario-test"
integration_test = "integration-test"
contract_test = "contract-test"
transition_test = "transition-test"
benchmark = "benchmark"

__all__ = [
    "ALL_TYPES",
    "acceptance_test",
    "benchmark",
    "business_concept",
    "code_ref",
    "confidential",
    "config_set",
    "configuration",
    "constraint",
    "contract_test",
    "dependency",
    "draft",
    "entity",
    "environment",
    "error",
    "event",
    "incident",
    "integration_test",
    "interface",
    "metric",
    "module",
    "orchestration",
    "permission",
    "pipeline",
    "playbook",
    "process",
    "reaction",
    "repository",
    "requirement",
    "role",
    "runbook",
    "scenario_test",
    "schedule",
    "transition_test",
    "user_story",
]

ALL_TYPES = (
    draft,
    requirement,
    user_story,
    business_concept,
    entity,
    interface,
    event,
    error,
    process,
    orchestration,
    reaction,
    schedule,
    repository,
    code_ref,
    incident,
    runbook,
    playbook,
    constraint,
    metric,
    role,
    permission,
    dependency,
    module,
    environment,
    pipeline,
    configuration,
    config_set,
    confidential,
    acceptance_test,
    scenario_test,
    integration_test,
    contract_test,
    transition_test,
    benchmark,
)
