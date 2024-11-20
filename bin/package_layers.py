# import os
# import shutil
# from pathlib import Path
# import zipfile
# import glob
# modules = ["authentication"]
# DEFAULT_LAYER_PATH = "layers"
# class PackageLayers:
#     def __init__(self):
#         self.modules = modules
#         self.setup()
#         for module in self.modules:
#             module_paths = self.map_packages_requirements(module)
#             if module_paths["module_path"]:
#                 self.create_module_structure(module_paths)
#     def setup(self):
#         """Set up the default layers directory."""
#         if not os.path.exists(DEFAULT_LAYER_PATH):
#             os.mkdir(DEFAULT_LAYER_PATH)
#     def create_module_structure(self, module: dict) -> None:
#         """Create module-specific folders and zip files."""
#         module_name = module["module_path"].name
#         module_layer_path = Path(f"{DEFAULT_LAYER_PATH}/{module_name}")
#         dependencies_path = module_layer_path / "dependencies"
#         module_code_path = module_layer_path / "module"
#         # Ensure the folder structure exists
#         dependencies_path.mkdir(parents=True, exist_ok=True)
#         module_code_path.mkdir(parents=True, exist_ok=True)
#         # Install and zip dependencies
#         self.zip_dependencies(module["requirements_path"], dependencies_path, module_name)
#         # Zip module source code
#         self.zip_module_source(module["module_path"], module_code_path)
#     def zip_dependencies(self, requirements_path: Path, dependencies_path: Path, module_name: str) -> None:
#         """Install dependencies and zip them."""
#         if requirements_path:
#             install_path = dependencies_path / "temp_dependencies"
#             os.makedirs(install_path, exist_ok=True)
#             try:
#                 print(f"Installing requirements from {requirements_path}")
#                 os.system(f"pip install -r {requirements_path} -t {install_path}")
#                 # Create dependencies.zip
#                 dependencies_zip_path = dependencies_path / f"{module_name}.zip"
#                 with zipfile.ZipFile(dependencies_zip_path, "w") as zf:
#                     for file_path in install_path.rglob("*"):
#                         zf.write(file_path, arcname=file_path.relative_to(install_path))
#                 print(f"Dependencies zipped to: {dependencies_zip_path}")
#             finally:
#                 # Clean up the temporary dependencies folder
#                 shutil.rmtree(install_path)
#         else:
#             print("No requirements found, skipping dependencies.")
#     def zip_module_source(self, module_path: Path, module_code_path: Path) -> None:
#         """Zip module source files."""
#         module_zip_path = module_code_path / f"{module_path.name}.zip"
#         with zipfile.ZipFile(module_zip_path, "w") as zf:
#             for file_path in module_path.rglob("*"):
#                 zf.write(file_path, arcname=file_path.relative_to(module_path.parent))
#         print(f"Module source zipped to: {module_zip_path}")
#     def map_packages_requirements(self, module_name: str) -> dict:
#         """Find the module path and requirements file."""
#         module_path = glob.glob(f"**/{module_name}/", recursive=True)
#         if module_path:
#             module_path = Path(module_path[0]).resolve()
#             requirements_path = glob.glob(str(module_path / "requirements.txt"))
#             if requirements_path:
#                 requirements_path = Path(requirements_path[0]).resolve()
#             else:
#                 requirements_path = None
#         else:
#             module_path = None
#             requirements_path = None
#         return {
#             "module_path": module_path,
#             "requirements_path": requirements_path
#         }
# # Run the script
# if __name__ == "__main__":
#     PackageLayers()
import glob
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

modules = ["authentication"]
DEFAULT_LAYER_PATH = "layers"


class PackageLayers:
    def __init__(self):
        self.modules = modules
        self.setup()
        for module in self.modules:
            module_paths = self.map_packages_requirements(module)
            if module_paths["module_path"]:
                self.create_module_structure(module_paths)

    def setup(self):
        """Set up the default layers directory."""
        if not os.path.exists(DEFAULT_LAYER_PATH):
            os.mkdir(DEFAULT_LAYER_PATH)

    def create_module_structure(self, module: dict) -> None:
        """Create module-specific folders and zip files."""
        module_name = module["module_path"].name
        module_layer_path = Path(f"{DEFAULT_LAYER_PATH}/{module_name}")

        # Install and zip dependencies
        # self.zip_dependencies(module["requirements_path"], dependencies_path, module_name)
        self.copy_module_files(module, module_layer_path)

        self.install_dependencies(module_layer_path)
        # Zip module source code
        # self.zip_module_source(module["module_path"], module_code_path)

    def install_dependencies(self, module_layer_path: Path) -> None:
        """Install dependencies"""

        subprocess.run(
            [
                "pip",
                "install",
                "-r",
                module_layer_path.absolute() / "requirements.txt",
                "-t",
                ".",
            ],
            check=True,
            cwd=module_layer_path,
        )

    def copy_module_files(self, src_module: dict, dest_path: dict) -> None:
        shutil.copytree(src_module["module_path"], dest_path)

    def zip_module_source(self, module_path: Path) -> None:
        module_zip_path = module_path.parent / f"{module_path.name}.zip"
        with zipfile.ZipFile(module_zip_path, "w") as zf:
            for file_path in module_path.rglob("*"):
                zf.write(file_path, arcname=file_path.relative_to(module_path.parent))
        print(f"Module source zipped to: {module_zip_path}")

    # def install_dependencies(self, requirements_path: Path, dependencies_path: Path, module_name: str) -> None:
    #     """Install dependencies"""
    #     if requirements_path:
    #         install_path = dependencies_path / ""
    #         os.makedirs(install_path, exist_ok=True)

    #         try:
    #             print(f"Installing requirements from {requirements_path}")
    #             os.system(f"pip install -r {requirements_path} -t {install_path}")

    #             # Create dependencies.zip
    #             # dependencies_zip_path = dependencies_path / f"{module_name}.zip"
    #             # with zipfile.ZipFile(dependencies_zip_path, "w") as zf:
    #             #     for file_path in install_path.rglob("*"):
    #             #         zf.write(file_path, arcname=file_path.relative_to(install_path))

    #             # print(f"Dependencies zipped to: {dependencies_zip_path}")
    #             print(f"Dependencies installed")
    #         finally:
    #             # Clean up the temporary dependencies folder
    #             shutil.rmtree(install_path)
    #     else:
    #         print("No requirements found, skipping dependencies.")

    def zip_module_source(self, module_path: Path, module_code_path: Path) -> None:
        """Zip module source files."""
        module_zip_path = module_code_path / f"{module_path.name}.zip"
        with zipfile.ZipFile(module_zip_path, "w") as zf:
            for file_path in module_path.rglob("*"):
                zf.write(file_path, arcname=file_path.relative_to(module_path.parent))
        print(f"Module source zipped to: {module_zip_path}")

    def map_packages_requirements(self, module_name: str) -> dict:
        """Find the module path and requirements file."""
        module_path = glob.glob(f"**/{module_name}/", recursive=True)

        if module_path:
            module_path = Path(module_path[0]).resolve()
            requirements_path = glob.glob(str(module_path / "requirements.txt"))
            if requirements_path:
                requirements_path = Path(requirements_path[0]).resolve()
            else:
                requirements_path = None
        else:
            module_path = None
            requirements_path = None

        return {"module_path": module_path, "requirements_path": requirements_path}


# Run the script
if __name__ == "__main__":
    PackageLayers()
