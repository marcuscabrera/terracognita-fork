package huaweicloud

import "fmt"

// ResourceType represents the supported Huawei Cloud resource identifiers.
type ResourceType string

const (
	ComputeInstance ResourceType = "huaweicloud_compute_instance"
	VPC             ResourceType = "huaweicloud_vpc"
	VPCSubnet       ResourceType = "huaweicloud_vpc_subnet"
	EIP             ResourceType = "huaweicloud_vpc_eip"
	EVSVolume       ResourceType = "huaweicloud_evs_volume"
	NatGateway      ResourceType = "huaweicloud_nat_gateway"
	OBSBucket       ResourceType = "huaweicloud_obs_bucket"
)

var resourceTypeValues = []ResourceType{
	ComputeInstance,
	VPC,
	VPCSubnet,
	EIP,
	EVSVolume,
	NatGateway,
	OBSBucket,
}

// ResourceTypeStrings returns the list of resource type strings supported by the Huawei Cloud provider.
func ResourceTypeStrings() []string {
	out := make([]string, len(resourceTypeValues))
	for i, v := range resourceTypeValues {
		out[i] = string(v)
	}
	return out
}

// ResourceTypeString validates that the provided string matches a supported resource type.
func ResourceTypeString(in string) (ResourceType, error) {
	for _, v := range resourceTypeValues {
		if string(v) == in {
			return v, nil
		}
	}
	return "", fmt.Errorf("unsupported resource type %q", in)
}
