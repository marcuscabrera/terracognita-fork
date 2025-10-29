package cmd

import (
	"fmt"

	"github.com/cycloidio/terracognita/huaweicloud"
	"github.com/spf13/cobra"
)

var (
	huaweicloudResourcesCmd = &cobra.Command{
		Use:   "resources",
		Short: "List of all the Huawei Cloud supported Resources",
		Run: func(cmd *cobra.Command, args []string) {
			for _, r := range huaweicloud.ResourceTypeStrings() {
				fmt.Println(r)
			}
		},
	}
)
