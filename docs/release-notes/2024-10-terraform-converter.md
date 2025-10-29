# October 2024 – Terraform configuration converter helpers

- Added `scripts/terraform_converter.py`, a Python module that translates Terraform configurations between AWS, Azure, Google Cloud and Huawei Cloud providers.
- Implemented per-provider conversion functions that validate required attributes and return detailed error messages when an automatic mapping is not possible.
- Documented usage instructions, dependencies and known limitations for the converter helpers in the project README.
