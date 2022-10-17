import os, sys
import pulumi
import pulumi.automation as auto
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs
from pulumi_kubernetes.core.v1 import ContainerArgs, PodSpecArgs, PodTemplateSpecArgs

project_name = os.environ.get("PROJECT_NAME")
stack_name = os.environ.get("STACK_NAME")


def create_pulumi_program(replicas: int = 5):
    app_labels = {"app": "nginx"}

    deployment = Deployment(
        "nginx",
        spec=DeploymentSpecArgs(
            selector=LabelSelectorArgs(match_labels=app_labels),
            replicas=replicas,
            template=PodTemplateSpecArgs(
                metadata=ObjectMetaArgs(labels=app_labels),
                spec=PodSpecArgs(
                    containers=[ContainerArgs(name="nginx", image="nginx")]
                ),
            ),
        ),
    )

    pulumi.export("name", deployment.metadata["name"])


def create_site():
    try:
        # create a new stack, generating our pulumi program on the fly from the POST body
        stack = auto.create_stack(
            stack_name=str(stack_name),
            project_name=project_name,
            program=create_pulumi_program,
        )
        # deploy the stack, tailing the logs to stdout
        stack.up(on_output=print)
        print(f"Successfully created site '{stack_name}'")
    except auto.StackAlreadyExistsError:
        print(
            f"Error: Site with name '{stack_name}' already exists, pick a unique name"
        )


def update_site(replicas: int = 5):
    def pulumi_program():
        create_pulumi_program(replicas)

    try:
        stack = auto.select_stack(
            stack_name=stack_name,
            project_name=project_name,
            program=pulumi_program,
        )
        # deploy the stack, tailing the logs to stdout
        stack.up(on_output=print)
        print(f"VM '{stack_name}' successfully updated!")
    except auto.ConcurrentUpdateError:
        print(f"Error: VM '{stack_name}' already has an update in progress")
    except Exception as e:
        print(str(e))


def delete_site():
    try:
        stack = auto.select_stack(
            stack_name=stack_name,
            project_name=project_name,
            # noop program for destroy
            program=lambda: None,
        )
        stack.destroy(on_output=print)
        stack.workspace.remove_stack(stack_name)
        print(f"VM '{stack_name}' successfully deleted!")
    except auto.ConcurrentUpdateError:
        print(f"Error: VM '{stack_name}' already has update in progress")
    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    # if len(sys.argv) > 1:
    #     update_site(int(sys.argv[1]))
    # else:
    #     update_site()
    create_site()
    # delete_site()
