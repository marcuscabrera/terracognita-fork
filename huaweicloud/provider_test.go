package huaweicloud

import (
	"context"
	"testing"
)

func TestNewProvider(t *testing.T) {
	ctx := context.Background()
	p, err := NewProvider(ctx, "cn-north-1", "123456", "access", "secret", "")
	if err != nil {
		t.Fatalf("unexpected error creating provider: %v", err)
	}

	if got, want := p.String(), "huaweicloud"; got != want {
		t.Fatalf("unexpected provider string: got %q want %q", got, want)
	}

	if got := p.Region(); got != "cn-north-1" {
		t.Fatalf("unexpected region: %s", got)
	}

	if !p.HasResourceType("huaweicloud_compute_instance") {
		t.Fatalf("expected resource type to be supported")
	}

	if len(p.ResourceTypes()) == 0 {
		t.Fatalf("expected ResourceTypes to be populated")
	}
}
