"""Utility functions to convert Terraform configurations between providers.

This module parses Terraform configuration files written in HCL or the official
Terraform JSON syntax and rewrites the resources using the closest equivalent
from another provider.  The conversion is intentionally conservative and
captures the most common IaaS building blocks such as virtual machines,
networks, subnets and security groups.  Whenever a resource cannot be mapped the
converter records a detailed error message explaining the limitation so
engineers can adjust the source configuration manually.

Usage example::

    from scripts.terraform_converter import convert_aws_to_huaweicloud
    report = convert_aws_to_huaweicloud(
        input_path="examples/aws/main.tf",
        output_path="out/huaweicloud.json"
    )
    print(report.successful_resources)
    print(report.errors)

The conversion output is written in Terraform JSON format to keep the
serialization deterministic across Python versions.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Tuple

try:  # Optional dependency used for HCL parsing.
    import hcl2  # type: ignore
except Exception:  # pragma: no cover - handled at runtime via error reporting.
    hcl2 = None


class ResourceConversionError(Exception):
    """Raised when a resource cannot be converted."""


@dataclass
class ConversionReport:
    """Summary of a conversion run."""

    successful_resources: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def raise_if_failed(self) -> None:
        if self.errors:
            raise ResourceConversionError("Conversion completed with errors:\n" + "\n".join(self.errors))


ResourceBody = Dict[str, Any]
ResourceEntry = Tuple[str, str, ResourceBody]
ConverterFn = Callable[[str, ResourceBody], List[ResourceEntry]]


def load_terraform_config(input_path: Path) -> Dict[str, Any]:
    """Load a Terraform configuration file in HCL or JSON format."""
    data = input_path.read_text(encoding="utf-8")
    if input_path.suffix.lower() == ".json":
        return json.loads(data)
    if hcl2 is None:
        raise RuntimeError(
            "The python-hcl2 package is required to parse HCL files. Install it with 'pip install python-hcl2'."
        )
    return hcl2.loads(data)


def dump_terraform_json(config: Dict[str, Any], output_path: Path) -> None:
    """Serialize the Terraform configuration as canonical JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")


def iter_resources(config: Dict[str, Any]) -> Iterable[ResourceEntry]:
    """Yield (type, name, body) tuples for every resource in the configuration."""
    resources = config.get("resource", {})
    if isinstance(resources, dict):
        for r_type, instances in resources.items():
            for name, body in instances.items():
                yield r_type, name, body
    elif isinstance(resources, list):
        for block in resources:
            if not isinstance(block, dict):
                continue
            for r_type, values in block.items():
                if isinstance(values, list):
                    for instance in values:
                        for name, body in instance.items():
                            yield r_type, name, body
                elif isinstance(values, dict):
                    for name, body in values.items():
                        yield r_type, name, body


def build_output_structure(resources: Iterable[Tuple[str, str, ResourceBody]], template: Dict[str, Any]) -> Dict[str, Any]:
    """Return a Terraform JSON document containing the provided resources."""
    output: Dict[str, Any] = {}
    for key, value in template.items():
        if key == "resource":
            continue
        output[key] = value

    resource_section: Dict[str, Dict[str, Any]] = {}
    for r_type, name, body in resources:
        resource_section.setdefault(r_type, {})[name] = body
    if resource_section:
        output["resource"] = resource_section
    return output


def convert_configuration(
    input_path: str,
    output_path: str,
    resource_converters: Dict[str, ConverterFn],
    provider_block: Dict[str, Any],
    unsupported_notice: str,
) -> ConversionReport:
    """General conversion helper used by provider specific wrappers."""
    input_file = Path(input_path)
    config = load_terraform_config(input_file)
    converted_resources: List[Tuple[str, str, ResourceBody]] = []
    report = ConversionReport()

    for r_type, name, body in iter_resources(config):
        converter = resource_converters.get(r_type)
        if converter is None:
            report.errors.append(
                f"Unsupported resource '{r_type}.{name}'. {unsupported_notice}".strip()
            )
            continue
        try:
            new_resources = converter(name, body)
        except ResourceConversionError as exc:  # type: ignore[no-redef]
            report.errors.append(f"{r_type}.{name}: {exc}")
            continue
        for new_type, new_name, new_body in new_resources:
            converted_resources.append((new_type, new_name, new_body))
            report.successful_resources.append(f"{new_type}.{new_name}")

    output_config = build_output_structure(converted_resources, config)
    if provider_block:
        output_config.setdefault("provider", {}).update(provider_block)

    dump_terraform_json(output_config, Path(output_path))
    return report


def _validate_fields(required_fields: Iterable[str], resource_name: str, body: ResourceBody) -> None:
    missing = [field for field in required_fields if field not in body]
    if missing:
        raise ResourceConversionError(
            f"Resource '{resource_name}' is missing required fields: {', '.join(missing)}"
        )


def _copy_common_fields(body: ResourceBody, allowed_fields: Iterable[str]) -> Dict[str, Any]:
    return {target: body[source] for source, target in allowed_fields if source in body}


# --- AWS -> Huawei Cloud -------------------------------------------------------------------------


def _convert_aws_instance(name: str, body: ResourceBody) -> List[ResourceEntry]:
    _validate_fields(["ami", "instance_type"], name, body)
    mapped = {
        "image_id": body["ami"],
        "flavor_name": body["instance_type"],
    }
    field_map = [
        ("subnet_id", "subnet_id"),
        ("associate_public_ip_address", "assign_public_ip"),
        ("key_name", "key_pair"),
        ("tags", "tags"),
    ]
    mapped.update(_copy_common_fields(body, field_map))
    if "vpc_security_group_ids" in body:
        mapped["security_groups"] = body["vpc_security_group_ids"]
    return [("huaweicloud_compute_instance", name, mapped)]


def _convert_aws_vpc(name: str, body: ResourceBody) -> List[ResourceEntry]:
    _validate_fields(["cidr_block"], name, body)
    mapped = {"cidr": body["cidr_block"]}
    mapped.update(_copy_common_fields(body, [("tags", "tags"), ("enable_dns_hostnames", "enable_dns_hostnames")]))
    return [("huaweicloud_vpc", name, mapped)]


def _convert_aws_subnet(name: str, body: ResourceBody) -> List[ResourceEntry]:
    _validate_fields(["vpc_id", "cidr_block"], name, body)
    mapped = {
        "vpc_id": body["vpc_id"],
        "cidr": body["cidr_block"],
    }
    mapped.update(_copy_common_fields(body, [("availability_zone", "availability_zone"), ("tags", "tags")]))
    return [("huaweicloud_vpc_subnet", name, mapped)]


def _convert_aws_security_group(name: str, body: ResourceBody) -> List[ResourceEntry]:
    mapped = _copy_common_fields(body, [("name", "name"), ("description", "description"), ("tags", "tags")])
    if any(key in body for key in ("ingress", "egress")):
        raise ResourceConversionError(
            "Security group rules must be migrated manually because Huawei Cloud manages them through "
            "separate huaweicloud_networking_secgroup_rule resources."
        )
    return [("huaweicloud_networking_secgroup", name, mapped)]


AWS_TO_HUAWEI_CONVERTERS: Dict[str, ConverterFn] = {
    "aws_instance": _convert_aws_instance,
    "aws_vpc": _convert_aws_vpc,
    "aws_subnet": _convert_aws_subnet,
    "aws_security_group": _convert_aws_security_group,
}


HUAWEI_PROVIDER_BLOCK = {
    "huaweicloud": {
        "region": "${var.huaweicloud_region}"}
}


# --- Azure -> AWS --------------------------------------------------------------------------------


def _convert_azure_vm(name: str, body: ResourceBody) -> List[ResourceEntry]:
    instance_type = body.get("vm_size") or body.get("size")
    if not instance_type:
        raise ResourceConversionError("Azure virtual machine definition is missing vm_size/size.")
    mapped: ResourceBody = {"instance_type": instance_type}
    os_disk = body.get("storage_os_disk") or body.get("os_disk") or {}
    image_reference = body.get("storage_image_reference") or body.get("source_image_reference") or {}
    ami = (
        image_reference.get("id")
        or image_reference.get("urn")
        or image_reference.get("publisher")
    )
    if ami:
        mapped["ami"] = ami
    else:
        raise ResourceConversionError(
            "Azure virtual machine is missing 'storage_image_reference.id' or '.urn' required to map to an AWS AMI."
        )
    nic_refs = body.get("network_interface_ids")
    if nic_refs:
        mapped["network_interface_ids"] = nic_refs
    tags = body.get("tags")
    if tags:
        mapped["tags"] = tags
    if os_disk.get("caching") == "ReadWrite":
        mapped.setdefault("root_block_device", {}).setdefault("delete_on_termination", True)
    return [("aws_instance", name, mapped)]


def _convert_azure_vnet(name: str, body: ResourceBody) -> List[ResourceEntry]:
    _validate_fields(["address_space"], name, body)
    spaces = body.get("address_space") or {}
    if isinstance(spaces, dict):
        cidrs = spaces.get("address_prefixes") or spaces.get("address_prefix")
    else:
        cidrs = spaces
    if not cidrs:
        raise ResourceConversionError("Virtual network must define at least one CIDR block.")
    mapped = {
        "cidr_block": cidrs[0] if isinstance(cidrs, list) else cidrs,
    }
    if tags := body.get("tags"):
        mapped["tags"] = tags
    return [("aws_vpc", name, mapped)]


def _convert_azure_subnet(name: str, body: ResourceBody) -> List[ResourceEntry]:
    _validate_fields(["address_prefix"], name, body)
    mapped = {
        "cidr_block": body["address_prefix"],
    }
    vnet_name = body.get("virtual_network_name")
    if isinstance(vnet_name, str):
        if "azurerm_virtual_network" in vnet_name:
            mapped["vpc_id"] = (
                vnet_name.replace("azurerm_virtual_network", "aws_vpc").replace(".name", ".id")
            )
        else:
            mapped["vpc_id"] = vnet_name
    else:
        raise ResourceConversionError(
            "Subnets must reference virtual_network_name so it can be mapped to the target VPC."
        )
    if tags := body.get("tags"):
        mapped["tags"] = tags
    return [("aws_subnet", name, mapped)]


def _convert_azure_nsg(name: str, body: ResourceBody) -> List[ResourceEntry]:
    mapped = _copy_common_fields(body, [("name", "name"), ("tags", "tags")])
    if body.get("security_rule"):
        raise ResourceConversionError(
            "Network security group rules cannot be translated automatically. Please recreate them using aws_security_group_rule."
        )
    return [("aws_security_group", name, mapped)]


AZURE_TO_AWS_CONVERTERS: Dict[str, ConverterFn] = {
    "azurerm_virtual_machine": _convert_azure_vm,
    "azurerm_linux_virtual_machine": _convert_azure_vm,
    "azurerm_virtual_network": _convert_azure_vnet,
    "azurerm_subnet": _convert_azure_subnet,
    "azurerm_network_security_group": _convert_azure_nsg,
}


AWS_PROVIDER_BLOCK = {
    "aws": {
        "region": "${var.aws_region}"}
}


# --- Google Cloud -> Azure -----------------------------------------------------------------------


def _convert_gcp_instance(name: str, body: ResourceBody) -> List[ResourceEntry]:
    _validate_fields(["machine_type"], name, body)
    boot_disk = body.get("boot_disk", {})
    if isinstance(boot_disk, list):
        boot_disk = boot_disk[0]
    image_params = boot_disk.get("initialize_params", {}) if isinstance(boot_disk, dict) else {}
    source_image = image_params.get("image")
    if not source_image:
        raise ResourceConversionError("Compute instance missing boot_disk.initialize_params.image for Azure conversion.")

    nic_name = f"{name}_nic"
    nic_body: ResourceBody = {
        "name": nic_name,
        "location": "${var.azure_location}",
        "resource_group_name": "${var.azure_resource_group}",
        "ip_configuration": [{
            "name": "primary",
            "subnet_id": "${var.azure_subnet_id}",
            "private_ip_address_allocation": "Dynamic",
            "public_ip_address_id": "${var.azure_public_ip_id}" if body.get("can_ip_forward") else None,
        }],
    }
    if isinstance(body.get("network_interface"), list):
        first = body["network_interface"][0]
        if isinstance(first, dict):
            subnet = first.get("subnetwork") or first.get("subnetwork_self_link")
            if subnet:
                nic_body["ip_configuration"][0]["subnet_id"] = subnet.replace(
                    "google_compute_subnetwork", "azurerm_subnet"
                ).replace("self_link", "id")
            if first.get("access_config"):
                nic_body["ip_configuration"][0]["public_ip_address_id"] = "${var.azure_public_ip_id}"

    vm_body: ResourceBody = {
        "name": name,
        "location": "${var.azure_location}",
        "resource_group_name": "${var.azure_resource_group}",
        "size": body["machine_type"],
        "admin_username": "${var.azure_admin_username}",
        "disable_password_authentication": True,
        "network_interface_ids": [f"${{azurerm_network_interface.{nic_name}.id}}"],
        "os_disk": {
            "name": f"{name}-os-disk",
            "caching": "ReadWrite",
            "storage_account_type": "Standard_LRS",
        },
        "source_image_id": source_image,
    }
    if tags := body.get("tags"):
        vm_body["tags"] = tags

    # Clean optional None entries from NIC configuration.
    ip_config = nic_body["ip_configuration"][0]
    if ip_config.get("public_ip_address_id") is None:
        ip_config.pop("public_ip_address_id")

    return [
        ("azurerm_network_interface", nic_name, nic_body),
        ("azurerm_linux_virtual_machine", name, vm_body),
    ]


def _convert_gcp_network(name: str, body: ResourceBody) -> List[ResourceEntry]:
    auto = body.get("auto_create_subnetworks", True)
    if auto:
        raise ResourceConversionError(
            "VPC networks with auto_create_subnetworks cannot be mapped to Azure VNets automatically."
        )
    address_prefixes = body.get("routing_config", {}).get("ipv4_cidr_blocks")
    if not address_prefixes:
        address_prefixes = ["${var.azure_vnet_cidr}"]
    mapped: ResourceBody = {
        "name": body.get("name", name),
        "location": "${var.azure_location}",
        "resource_group_name": "${var.azure_resource_group}",
        "address_space": address_prefixes,
    }
    return [("azurerm_virtual_network", name, mapped)]


def _convert_gcp_subnetwork(name: str, body: ResourceBody) -> List[ResourceEntry]:
    _validate_fields(["ip_cidr_range"], name, body)
    network_ref = body.get("network") or "${var.azure_vnet_name}"
    if isinstance(network_ref, str) and "google_compute_network" in network_ref:
        network_ref = network_ref.replace("google_compute_network", "azurerm_virtual_network").replace(".name", "")
    mapped: ResourceBody = {
        "name": body.get("name", name),
        "resource_group_name": "${var.azure_resource_group}",
        "virtual_network_name": network_ref if isinstance(network_ref, str) else "${var.azure_vnet_name}",
        "address_prefixes": [body["ip_cidr_range"]],
    }
    if region := body.get("region"):
        mapped["delegation"] = [
            {
                "name": f"{name}-delegation",
                "service_delegation": {"name": f"Microsoft.Network/{region}"},
            }
        ]
    return [("azurerm_subnet", name, mapped)]


def _convert_gcp_firewall(name: str, body: ResourceBody) -> List[ResourceEntry]:
    raise ResourceConversionError(
        "GCP firewall rules must be recreated manually using azurerm_network_security_group_rule."
    )


GCP_TO_AZURE_CONVERTERS: Dict[str, ConverterFn] = {
    "google_compute_instance": _convert_gcp_instance,
    "google_compute_network": _convert_gcp_network,
    "google_compute_subnetwork": _convert_gcp_subnetwork,
    "google_compute_firewall": _convert_gcp_firewall,
}


AZURE_PROVIDER_BLOCK = {
    "azurerm": {
        "features": {}},
}


def convert_aws_to_huaweicloud(input_path: str, output_path: str) -> ConversionReport:
    """Convert Terraform resources from AWS to Huawei Cloud."""
    return convert_configuration(
        input_path,
        output_path,
        AWS_TO_HUAWEI_CONVERTERS,
        HUAWEI_PROVIDER_BLOCK,
        "No equivalent Huawei Cloud resource is available in the automated converter yet.",
    )


def convert_azure_to_aws(input_path: str, output_path: str) -> ConversionReport:
    """Convert Terraform resources from AzureRM to AWS."""
    return convert_configuration(
        input_path,
        output_path,
        AZURE_TO_AWS_CONVERTERS,
        AWS_PROVIDER_BLOCK,
        "Please update scripts/terraform_converter.py with the missing Azure resource mapping.",
    )


def convert_gcp_to_azure(input_path: str, output_path: str) -> ConversionReport:
    """Convert Terraform resources from Google Cloud to Azure."""
    return convert_configuration(
        input_path,
        output_path,
        GCP_TO_AZURE_CONVERTERS,
        AZURE_PROVIDER_BLOCK,
        "The converter currently supports compute instances, networks and basic tags.",
    )


__all__ = [
    "ConversionReport",
    "ResourceConversionError",
    "convert_aws_to_huaweicloud",
    "convert_azure_to_aws",
    "convert_gcp_to_azure",
]
