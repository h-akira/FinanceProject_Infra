# CDK Bootstrap用の初期設定

このディレクトリには、CDKのCloudFormation実行ロールにカスタム権限を付与するためのCloudFormationテンプレートが含まれています。

## 概要

CDKでは、デプロイ時に**2つの異なるロール**が使用されます:

1. **CDK実行者（開発者/CI-CD）**: CloudFormationスタックの作成・更新操作のみを実行
2. **CloudFormation実行ロール**: 実際のAWSリソース（Cognito、S3、Lambda等）を作成・削除

デフォルトのCDK bootstrapでは、CloudFormation実行ロールに`PowerUserAccess`（管理者権限に近い広範な権限）が付与されますが、これは**セキュリティ上推奨されません**。

このテンプレートは、FinanceProjectで実際に必要な最小限の権限のみを定義したカスタムポリシーを作成します。

## 付与される権限

このポリシーが許可するAWSサービス:

| サービス | 用途 | スコープ |
|---------|------|---------|
| **Cognito** | User Pool/Client作成 | User Poolのみ |
| **S3** | バケット作成・管理 | 全バケット（CDKが管理） |
| **CloudFront** | Distribution作成・管理 | 全リソース（必須） |
| **ACM** | 証明書参照（読み取り専用） | 全リソース（読み取りのみ） |
| **SSM Parameter Store** | パラメータ作成・管理 | 全パラメータ |
| **IAM** | ロール・ポリシー作成 | 全ロール（PassRoleは制限付き） |
| **CodeBuild** | プロジェクト作成・管理 | 全プロジェクト |
| **CodeConnections** | GitHub接続参照 | 全接続（読み取りのみ） |
| **CloudWatch Logs** | ロググループ作成・管理 | 全ロググループ |
| **Lambda** | 関数作成・管理 | 全関数 |
| **API Gateway** | REST API作成・管理 | 全API |
| **CloudFormation** | ネストされたスタック管理 | 全スタック |
| **Application Insights** | SAMモニタリング | 全リソース |
| **Resource Groups** | SAMリソースグループ | 全グループ |

### PowerUserAccessとの比較

| 項目 | PowerUserAccess | カスタムポリシー |
|------|-----------------|-----------------|
| 権限範囲 | ほぼ全てのAWSサービス | 必要なサービスのみ |
| IAM操作 | ポリシー作成不可 | 必要な操作のみ許可 |
| セキュリティ | 広すぎる | 最小権限の原則に準拠 |
| 監査 | 困難 | 明確（YAMLで定義） |

## デプロイ手順

### 1. カスタムポリシーをデプロイ

```bash
cd /Users/hakira/Programs/wambda-develop/FinanceProject_Infra/init

AWS_PROFILE=finance aws cloudformation deploy \
  --template-file cfn-execution-policies.yaml \
  --stack-name stack-cdk-exec-policies \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1
```

**CAPABILITY_NAMED_IAM**: IAM Managed Policyを作成するために必要

### 2. ポリシーARNを確認

```bash
# ポリシーARNを取得
POLICY_ARN=$(AWS_PROFILE=finance aws cloudformation describe-stacks \
  --stack-name stack-cdk-exec-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`PolicyArn`].OutputValue' \
  --output text)

echo "Policy ARN: ${POLICY_ARN}"
```

出力例:
```
Policy ARN: arn:aws:iam::355202574892:policy/CDKCloudFormationExecutionPolicy-Finance
```

### 3. CDK Bootstrapでカスタムポリシーを指定

**新規環境の場合**:
```bash
# ポリシーARNを動的に取得してbootstrap
POLICY_ARN=$(AWS_PROFILE=finance aws cloudformation describe-stacks \
  --stack-name stack-cdk-exec-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`PolicyArn`].OutputValue' \
  --output text)

AWS_PROFILE=finance cdk bootstrap \
  --cloudformation-execution-policies ${POLICY_ARN} \
  --region ap-northeast-1
```

**既存のbootstrap環境を更新する場合**:
```bash
# ポリシーARNを取得
POLICY_ARN=$(AWS_PROFILE=finance aws cloudformation describe-stacks \
  --stack-name stack-cdk-exec-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`PolicyArn`].OutputValue' \
  --output text)

# 既存のbootstrapスタックを削除（注意: CDKで管理されているリソースがある場合は削除しないこと）
AWS_PROFILE=finance aws cloudformation delete-stack \
  --stack-name CDKToolkit \
  --region ap-northeast-1

# 新しいポリシーでbootstrap
AWS_PROFILE=finance cdk bootstrap \
  --cloudformation-execution-policies ${POLICY_ARN} \
  --region ap-northeast-1
```

### 4. 確認

```bash
# CloudFormation実行ロールを確認
AWS_PROFILE=finance aws iam get-role \
  --role-name cdk-hnb659fds-cfn-exec-role-XXXXXXXXXXXX-ap-northeast-1

# アタッチされているポリシーを確認
AWS_PROFILE=finance aws iam list-attached-role-policies \
  --role-name cdk-hnb659fds-cfn-exec-role-XXXXXXXXXXXX-ap-northeast-1
```

出力に`CDKCloudFormationExecutionPolicy-Finance`が含まれていればOK。

## ポリシーの更新

新しいAWSサービスを使用する場合、ポリシーを更新する必要があります。

### 1. cfn-execution-policies.yamlを編集

必要な権限を追加します。

### 2. スタックを更新

```bash
cd /Users/hakira/Programs/wambda-develop/FinanceProject_Infra/init

AWS_PROFILE=finance aws cloudformation deploy \
  --template-file cfn-execution-policies.yaml \
  --stack-name stack-cdk-exec-policies \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1
```

**重要**: ポリシーは自動的に既存のCloudFormation実行ロールに反映されます（Managed Policyのため）。Bootstrap再実行は不要です。

### 3. 変更内容を確認

```bash
AWS_PROFILE=finance aws iam get-policy-version \
  --policy-arn arn:aws:iam::XXXXXXXXXXXX:policy/CDKCloudFormationExecutionPolicy-Finance \
  --version-id v2  # バージョンは増加します
```

## トラブルシューティング

### デプロイ時に権限エラーが発生する

**エラー例**:
```
User: arn:aws:sts::XXXXXXXXXXXX:assumed-role/cdk-hnb659fds-cfn-exec-role-XXXXXXXXXXXX-ap-northeast-1/AWSCloudFormation is not authorized to perform: xxx:CreateXXX
```

**原因**: CloudFormation実行ロールに必要な権限が不足

**対処法**:
1. `cfn-execution-policies.yaml`に不足している権限を追加
2. スタックを更新（上記「ポリシーの更新」参照）
3. CDKデプロイを再実行

### PowerUserAccessに戻したい場合

```bash
# ポリシースタックを削除
AWS_PROFILE=finance aws cloudformation delete-stack \
  --stack-name stack-cdk-exec-policies \
  --region ap-northeast-1

# Bootstrap環境を削除
AWS_PROFILE=finance aws cloudformation delete-stack \
  --stack-name CDKToolkit \
  --region ap-northeast-1

# デフォルトでbootstrap（PowerUserAccessが使用される）
AWS_PROFILE=finance cdk bootstrap --region ap-northeast-1
```

## ベストプラクティス

1. **開発環境**: PowerUserAccessでも可（迅速な開発優先）
2. **本番環境**: カスタムポリシー必須（セキュリティ優先）
3. **定期的な監査**: 不要な権限が含まれていないか定期的にレビュー
4. **バージョン管理**: cfn-execution-policies.yamlは必ずGit管理する
5. **変更記録**: ポリシー変更時は理由をコミットメッセージに記載

## 参考資料

- [AWS CDK Bootstrap](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html)
- [CloudFormation Execution Policies](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html#bootstrapping-customizing)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Learning/06_権限管理編.md](../Learning/06_権限管理編.md)
