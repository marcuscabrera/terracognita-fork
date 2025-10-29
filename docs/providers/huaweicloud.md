# Huawei Cloud provider

The Huawei Cloud integration wraps the official Terraform provider to discover compute, networking and storage resources and export them as Terraform configuration/state.

## Prerequisites

* Enable the Huawei Cloud APIs for the projects that you want to import.
* Create an access key/secret key pair with read permissions for ECS, VPC, EVS, EIP, NAT Gateway and OBS.
* Export the standard Terraform provider environment variables:
  * `HW_ACCESS_KEY` / `HW_SECRET_KEY`
  * `HW_SECURITY_TOKEN` (only when using temporary credentials)
  * `HW_REGION_NAME`
  * `HW_PROJECT_ID`

You can also provide the same values via the CLI flags described below.

## Command usage

```bash
terracognita huaweicloud \
  --huaweicloud-access-key "$HW_ACCESS_KEY" \
  --huaweicloud-secret-key "$HW_SECRET_KEY" \
  --huaweicloud-project-id "$HW_PROJECT_ID" \
  --huaweicloud-region "$HW_REGION_NAME" \
  --include huaweicloud_compute_instance \
  --tags "environment:production" \
  --hcl ./hcl \
  --tfstate ./terraform.tfstate
```

### Supported resource types

The current implementation exposes the following resource identifiers:

* `huaweicloud_compute_instance`
* `huaweicloud_vpc`
* `huaweicloud_vpc_subnet`
* `huaweicloud_vpc_eip`
* `huaweicloud_evs_volume`
* `huaweicloud_nat_gateway`
* `huaweicloud_obs_bucket`

Each entry respects the filtering semantics already implemented in the shared provider logic.

## Notes

* Attribute introspection falls back to Terraform schemas when tfdocs metadata is not available.
* Tag filters use the generic `tags` key shared with other providers.
* State/HCL writers and module interpolation features operate with the same options available for other cloud providers.
