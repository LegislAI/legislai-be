import argparse
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
LOG = logging.getLogger(__name__)


# Terraform init
def terraform_init(module_path: Path):
    subprocess.run(["terraform", "init"], cwd=module_path, check=True)
    LOG.info("Terraform init completed.")


# Terraform plan
def terraform_plan(module_path: Path):
    subprocess.run(["terraform", "plan"], cwd=module_path, check=True)
    LOG.info("Terraform plan completed.")


# Terraform apply
def terraform_apply(module_path: Path):
    subprocess.run(["terraform", "apply", "-auto-approve"], cwd=module_path, check=True)
    LOG.info("Terraform apply completed.")


# Create Docker image for the API
def create_docker_image(docker_file_path: Path, module_path: Path, image_name: str):
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
            str(module_path),
            "--progress=plain",
            "-f",
            str(docker_file_path),
            "-t",
            image_name,
        ],
        check=True,
    )
    LOG.info("Docker image created.")


# Push Docker image to ECR
def push_docker_image_to_ecr(image_name: str, ecr_repository: str, aws_region: str):
    subprocess.run(
        f"aws ecr get-login-password --region {aws_region} | "
        f"docker login --username AWS --password-stdin {ecr_repository}",
        shell=True,
        check=True,
    )
    subprocess.run(
        f"docker tag {image_name}: latest {ecr_repository}/{image_name}: latest",
        shell=True,
        check=True,
    )
    subprocess.run(
        f"docker push {ecr_repository}/{image_name}: latest",
        shell=True,
        check=True,
    )
    LOG.info("Docker image pushed to ECR.")


# Deploy the API to ECS
def deploy_to_ecs(cluster_name: str, service_name: str):
    subprocess.run(
        f"aws ecs update-service --cluster {cluster_name} --service {service_name} --force-new-deployment",
        shell=True,
        check=True,
    )
    LOG.info("API deployed to ECS.")


def terraform_destroy(module_path: Path):
    subprocess.run(
        ["terraform", "destroy", "-auto-approve"], cwd=module_path, check=True
    )
    LOG.info("Terraform destroy completed.")


# Main function with argument parsing
def main():
    parser = argparse.ArgumentParser(
        description="Deploy the API using Terraform, Docker, and AWS ECS."
    )

    # Arguments
    parser.add_argument(
        "--module-path", type=str, required=True, help="Path to the Terraform module."
    )
    parser.add_argument(
        "--dockerfile-path", type=str, required=True, help="Path to the Dockerfile."
    )
    parser.add_argument(
        "--ecr-repository", type=str, required=True, help="ECR repository URL."
    )
    parser.add_argument(
        "--aws-region", type=str, required=True, help="AWS region for ECR."
    )
    parser.add_argument(
        "--cluster-name", type=str, required=True, help="ECS cluster name."
    )
    parser.add_argument(
        "--service-name", type=str, required=True, help="ECS service name."
    )
    parser.add_argument(
        "--image-name", type=str, required=False, help="Docker image name."
    )
    parser.add_argument(
        "--run-type",
        type=str,
        required=False,
        help="Type of run: 'full','tf_deploy','tf_destroy' or 'push_image.",
    )

    args = parser.parse_args()

    if args.run_type == "tf_deploy":
        LOG.info("Deploying Terraform resources.")
        terraform_init(Path(args.module_path))
        terraform_plan(Path(args.module_path))
        terraform_apply(Path(args.module_path))

    if args.run_type == "push_image":
        LOG.info("Building and pushing Docker image.")
        create_docker_image(
            Path(args.dockerfile_path), Path(args.module_path), args.image_name
        )
        push_docker_image_to_ecr(
            "authorizationimage", args.ecr_repository, args.aws_region
        )

    if args.run_type == "tf_destroy":
        LOG.info("Destroying Terraform resources.")
        terraform_destroy(Path(args.module_path))

    # Run Terraform commands
    terraform_init(Path(args.module_path))
    terraform_plan(Path(args.module_path))
    terraform_apply(Path(args.module_path))

    # Build and push Docker image
    create_docker_image(
        Path(args.dockerfile_path), Path(args.module_path), args.image_name
    )
    push_docker_image_to_ecr("authorizationimage", args.ecr_repository, args.aws_region)

    # Deploy to ECS
    deploy_to_ecs(args.cluster_name, args.service_name)


if __name__ == "__main__":
    main()
