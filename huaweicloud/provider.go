package huaweicloud

import (
	"context"

	"github.com/cycloidio/terracognita/cache"
	"github.com/cycloidio/terracognita/filter"
	"github.com/cycloidio/terracognita/log"
	"github.com/cycloidio/terracognita/provider"
	"github.com/hashicorp/go-cty/cty"
	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/schema"
	tfhuaweicloud "github.com/huaweicloud/terraform-provider-huaweicloud/huaweicloud"
	"github.com/pkg/errors"
)

// version of the Terraform provider.
const version = "1.78.0"

type huaweicloudProvider struct {
	tfProvider *schema.Provider
	tfClient   interface{}

	configuration map[string]interface{}

	cache cache.Cache
}

// NewProvider returns a Huawei Cloud Provider implementation.
func NewProvider(ctx context.Context, region, projectID, accessKey, secretKey, securityToken string) (provider.Provider, error) {
	log.Get().Log("func", "huaweicloud.NewProvider", "msg", "configuring TF Provider")

	tfp := tfhuaweicloud.Provider()

	config := map[string]interface{}{}
	if region != "" {
		config["region"] = region
	}
	if projectID != "" {
		config["project_id"] = projectID
	}
	if accessKey != "" {
		config["access_key"] = accessKey
	}
	if secretKey != "" {
		config["secret_key"] = secretKey
	}
	if securityToken != "" {
		config["security_token"] = securityToken
	}

	cfg := map[string]interface{}{}
	if region != "" {
		cfg["region"] = region
	}
	if projectID != "" {
		cfg["project_id"] = projectID
	}

	return &huaweicloudProvider{
		tfProvider:    tfp,
		tfClient:      config,
		configuration: cfg,
		cache:         cache.New(),
	}, nil
}

func (p *huaweicloudProvider) ResourceTypes() []string {
	return ResourceTypeStrings()
}

func (p *huaweicloudProvider) Resources(ctx context.Context, t string, f *filter.Filter) ([]provider.Resource, error) {
	rt, err := ResourceTypeString(t)
	if err != nil {
		return nil, err
	}

	rfn, ok := resources[rt]
	if !ok {
		return nil, errors.Errorf("the resource %q is not implemented", t)
	}

	res, err := rfn(ctx, p, t, f)
	if err != nil {
		return nil, errors.Wrapf(err, "error while reading from resource %q", t)
	}

	return res, nil
}

func (p *huaweicloudProvider) TFClient() interface{} {
	return p.tfClient
}

func (p *huaweicloudProvider) TFProvider() *schema.Provider {
	return p.tfProvider
}

func (p *huaweicloudProvider) String() string {
	return "huaweicloud"
}

func (p *huaweicloudProvider) Region() string {
	if v, ok := p.configuration["region"].(string); ok {
		return v
	}
	return ""
}

func (p *huaweicloudProvider) TagKey() string {
	return "tags"
}

func (p *huaweicloudProvider) HasResourceType(t string) bool {
	_, err := ResourceTypeString(t)
	return err == nil
}

func (p *huaweicloudProvider) Source() string {
	return "hashicorp/huaweicloud"
}

func (p *huaweicloudProvider) Version() string {
	return version
}

func (p *huaweicloudProvider) Configuration() map[string]interface{} {
	return p.configuration
}

func (p *huaweicloudProvider) FixResource(t string, v cty.Value) (cty.Value, error) {
	return v, nil
}

func (p *huaweicloudProvider) FilterByTags(tags interface{}) error {
	return nil
}
