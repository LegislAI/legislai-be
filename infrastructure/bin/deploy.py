#!/usr/bin/env/python3
import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
LOG = logging.getLogger(__name__)


def terraform_init(module_path: Path):
    subprocess.run(["terraform", "init"], cwd=module_path, check=True)
    LOG.info("Terraform init completed.")


def terraform_plan(module_path: Path):
    subprocess.run(["terraform", "plan"], cwd=module_path, check=True)
    LOG.info("Terraform plan completed.")


def terraform_apply(module_path: Path):
    subprocess.run(["terraform", "apply", "-auto-approve"], cwd=module_path, check=True)
    LOG.info("Terraform apply completed.")


def create_docker_image(
    docker_file_path: Path, source_code_path: Path, image_name: str
):
    subprocess.run(
        [
            "docker",
            "build",
            "--ssh",
            "default",
            "--platform",
            "linux/x86_64",
            "--no-cache",
            "--pull",
            str(source_code_path),
            "--progress=plain",
            "-f",
            str(docker_file_path),
            "-t",
            image_name,
        ],
        check=True,
    )
    LOG.info("Docker image created.")


def push_docker_image_to_ecr(image_name: str, ecr_repository: str, aws_region: str):
    LOG.info(f"Pushing Docker image to ECR in region {aws_region}...")
    subprocess.run(
        f"aws ecr get-login-password --region {aws_region} | docker login --username AWS --password-stdin {ecr_repository}",
        check=True,
        capture_output=True,
        text=True,
        shell=True,
    )
    subprocess.run(
        ["docker", "tag", f"{image_name}:latest", f"{ecr_repository}:latest"],
        check=True,
    )
    subprocess.run(["docker", "push", f"{ecr_repository}:latest"], check=True)
    LOG.info("Docker image pushed to ECR.")


def deploy_to_ecs(cluster_name: str, service_name: str):
    subprocess.run(
        [
            "aws",
            "ecs",
            "update-service",
            "--cluster",
            cluster_name,
            "--service",
            service_name,
            "--force-new-deployment",
        ],
        check=True,
    )
    LOG.info("API deployed to ECS.")


def terraform_destroy(module_path: Path):
    subprocess.run(
        ["terraform", "destroy", "-auto-approve"], cwd=module_path, check=True
    )
    LOG.info("Terraform destroy completed.")


def get_terraform_output(module_path: Path, output_name: str):
    result = subprocess.run(
        ["terraform", "output", "-json", output_name],
        cwd=module_path,
        check=True,
        capture_output=True,
        text=True,
    )
    output_value = json.loads(result.stdout)
    return output_value


def main():
    parser = argparse.ArgumentParser(
        description="Deploy the API using Terraform, Docker, and AWS ECS."
    )

    parser.add_argument(
        "--module-name", type=str, required=True, help="Name of the module to deploy."
    )
    parser.add_argument(
        "--run-type",
        type=str,
        required=True,
        help="Type of run: 'full', 'tf_deploy', 'tf_destroy', or 'push_image'.",
    )
    parser.add_argument("--aws-region", type=str, help="AWS region for ECR.")
    parser.add_argument("--cluster-name", type=str, help="ECS cluster name.")
    parser.add_argument("--service-name", type=str, help="ECS service name.")

    args = parser.parse_args()
    module_name = args.module_name

    module_path = Path(f"./terraform")
    dockerfile_path = module_path / f"modules/{module_name}/Dockerfile"
    source_code_path = Path(f"../{module_name}")
    image_name = module_name.lower()

    if (
        not module_path.exists()
        or not dockerfile_path.exists()
        or not source_code_path.exists()
    ):
        LOG.error(
            f"Module path, Dockerfile, or source code path is missing for module '{module_name}'."
        )
        sys.exit(1)

    if args.run_type == "tf_deploy":
        LOG.info("Deploying Terraform resources.")
        terraform_init(module_path)
        terraform_plan(module_path)
        terraform_apply(module_path)

    elif args.run_type == "push_image":
        if not args.aws_region:
            LOG.error("AWS region is required for pushing the image.")
            sys.exit(1)
        LOG.info("Building and pushing Docker image.")
        create_docker_image(dockerfile_path, source_code_path, image_name)

        ecr_repository_url = get_terraform_output(module_path, "ecr_repository_url")
        push_docker_image_to_ecr(image_name, ecr_repository_url, aws_region)

    elif args.run_type == "tf_destroy":
        LOG.info("Destroying Terraform resources.")
        terraform_destroy(module_path)

    elif args.run_type == "full":
        LOG.info("Running full deployment.")
        terraform_init(module_path)
        terraform_plan(module_path)
        terraform_apply(module_path)

        if not args.aws_region:
            aws_region = "eu-west-1"

        ecr_repository_url = get_terraform_output(module_path, "ecr_repository_url")

        create_docker_image(dockerfile_path, source_code_path, image_name)
        push_docker_image_to_ecr(image_name, ecr_repository_url, aws_region)

        if args.cluster_name and args.service_name:
            deploy_to_ecs(args.cluster_name, args.service_name)

    else:
        LOG.error(
            "Invalid run type specified. Choose 'full', 'tf_deploy', 'tf_destroy', or 'push_image'."
        )


if __name__ == "__main__":
    main()
