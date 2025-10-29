package cmd

import (
	"context"

	kitlog "github.com/go-kit/kit/log"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"github.com/cycloidio/terracognita/huaweicloud"
	"github.com/cycloidio/terracognita/log"
)

var (
	huaweicloudTags []string

	huaweicloudCmd = &cobra.Command{
		Use:   "huaweicloud",
		Short: "Terracognita reads from Huawei Cloud and generates hcl resources and/or terraform state",
		Long:  "Terracognita reads from Huawei Cloud and generates hcl resources and/or terraform state",
		PreRunE: func(cmd *cobra.Command, args []string) error {
			if err := preRunEOutput(cmd, args); err != nil {
				return err
			}

			viper.BindPFlag("huaweicloud-access-key", cmd.Flags().Lookup("huaweicloud-access-key"))
			viper.BindPFlag("huaweicloud-secret-key", cmd.Flags().Lookup("huaweicloud-secret-key"))
			viper.BindPFlag("huaweicloud-security-token", cmd.Flags().Lookup("huaweicloud-security-token"))
			viper.BindPFlag("huaweicloud-region", cmd.Flags().Lookup("huaweicloud-region"))
			viper.BindPFlag("huaweicloud-project-id", cmd.Flags().Lookup("huaweicloud-project-id"))
			viper.BindPFlag("tags", cmd.Flags().Lookup("tags"))

			viper.RegisterAlias("access-key", "huaweicloud-access-key")
			viper.RegisterAlias("secret-key", "huaweicloud-secret-key")
			viper.RegisterAlias("security-token", "huaweicloud-security-token")
			viper.RegisterAlias("region", "huaweicloud-region")
			viper.RegisterAlias("project-id", "huaweicloud-project-id")

			return nil
		},
		PostRunE: postRunEOutput,
		RunE: func(cmd *cobra.Command, args []string) error {
			logger := log.Get()
			logger = kitlog.With(logger, "func", "cmd.huaweicloud.RunE")

			if err := requiredStringFlags("access-key", "secret-key", "region", "project-id"); err != nil {
				return err
			}

			tags, err := initializeTags("tags")
			if err != nil {
				return err
			}

			ctx := context.Background()

			provider, err := huaweicloud.NewProvider(
				ctx,
				viper.GetString("region"),
				viper.GetString("project-id"),
				viper.GetString("access-key"),
				viper.GetString("secret-key"),
				viper.GetString("security-token"),
			)
			if err != nil {
				return err
			}

			if err := importProvider(ctx, logger, provider, tags); err != nil {
				return err
			}

			return nil
		},
	}
)

func init() {
	huaweicloudCmd.AddCommand(huaweicloudResourcesCmd)

	huaweicloudCmd.Flags().String("huaweicloud-access-key", "", "Access Key (required)")
	huaweicloudCmd.Flags().String("huaweicloud-secret-key", "", "Secret Key (required)")
	huaweicloudCmd.Flags().String("huaweicloud-security-token", "", "Security Token for temporary credentials")
	huaweicloudCmd.Flags().String("huaweicloud-region", "", "Region to search in (required)")
	huaweicloudCmd.Flags().String("huaweicloud-project-id", "", "Project ID scope for API calls (required)")

	huaweicloudCmd.Flags().StringSliceVarP(&huaweicloudTags, "tags", "t", []string{}, "List of tags to filter with format 'NAME:VALUE'")
}
