package huaweicloud

import (
	"context"

	"github.com/cycloidio/terracognita/filter"
	"github.com/cycloidio/terracognita/provider"
)

type resourceReader func(ctx context.Context, p *huaweicloudProvider, resourceType string, f *filter.Filter) ([]provider.Resource, error)

var resources = map[ResourceType]resourceReader{
	ComputeInstance: emptyResourceReader,
	VPC:             emptyResourceReader,
	VPCSubnet:       emptyResourceReader,
	EIP:             emptyResourceReader,
	EVSVolume:       emptyResourceReader,
	NatGateway:      emptyResourceReader,
	OBSBucket:       emptyResourceReader,
}

func emptyResourceReader(ctx context.Context, p *huaweicloudProvider, resourceType string, f *filter.Filter) ([]provider.Resource, error) {
	return []provider.Resource{}, nil
}
