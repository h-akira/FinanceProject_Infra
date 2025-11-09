# Finance Project Infrastructure CDK

AWS CDK (Python)によるFinance Projectのインフラストラクチャ定義です。
Terraform版(`FinanceProject_Infra`)と同じリソースをCDKで実装しています。

## 📚 学習教材

CDKの学習教材を用意しています。本プロジェクトを題材にして、CDKの基礎から実践まで学べます。

詳しくは → **[Learning/README.md](Learning/README.md)**

### 教材の内容
- **01_CDK基礎.md** - CDKとは何か？基本概念
- **02_Stack編.md** - Stackの詳細とスタック間の依存関係
- **03_Construct編.md** - ConstructのレベルとAPIの使い分け
- **04_実践編.md** - 本プロジェクトを題材にした実践的な使い方
- **05_Tips編.md** - よくあるパターンと注意点
- **06_権限管理編.md** - CDK実行に必要な権限の詳細

---

## 構成

```
FinanceProject_Infra/
├── stacks/
│   ├── common/
│   │   └── cognito_stack.py      # Cognito User Pool & Client
│   └── dashboard/
│       ├── main_stack.py         # S3 + CloudFront
│       └── dynamodb_stack.py     # DynamoDB Table
├── app.py                        # CDKアプリケーションエントリーポイント
├── config.json                   # 設定ファイル（環境変数、リソース名など）
├── cdk.json                      # CDK設定
└── requirements.txt              # Python依存関係
```

## セットアップ

### 前提条件

- Python 3.11以上
- Node.js（CDK CLI用）
- AWS CLI設定済み（`aws configure`または`~/.aws/credentials`）
- AWS_PROFILE=financeの設定（本プロジェクトでは`finance`プロファイルを使用）

### 1. CDK CLIのインストール

```bash
npm install -g aws-cdk
cdk --version
```

### 2. Python仮想環境の作成と有効化

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate.bat
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. CDK Bootstrap（初回のみ）

CDKを初めて使用する環境では、`cdk bootstrap`を実行する必要があります。

#### 推奨：カスタムポリシーを使用（セキュリティ重視）

まず、最小権限のカスタムポリシーをデプロイします：

```bash
cd /Users/hakira/Programs/wambda-develop/FinanceProject_Infra/init

AWS_PROFILE=finance aws cloudformation deploy \
  --template-file cfn-execution-policies.yaml \
  --stack-name stack-cdk-exec-policies \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1
```

次に、カスタムポリシーを使用してCDK bootstrapを実行します：

```bash
# ポリシーARNを動的に取得
POLICY_ARN=$(AWS_PROFILE=finance aws cloudformation describe-stacks \
  --stack-name stack-cdk-exec-policies \
  --region ap-northeast-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`PolicyArn`].OutputValue' \
  --output text)

# Bootstrap実行
AWS_PROFILE=finance cdk bootstrap \
  --cloudformation-execution-policies ${POLICY_ARN} \
  --region ap-northeast-1
```

#### 代替案：デフォルトのPowerUserAccess（開発環境のみ）

```bash
# 開発環境の場合のみ使用可能
AWS_PROFILE=finance cdk bootstrap \
  --cloudformation-execution-policies arn:aws:iam::aws:policy/PowerUserAccess
```

**⚠️ PowerUserAccessは広すぎる権限です。本番環境では必ずカスタムポリシーを使用してください。**

**注意**: `cdk bootstrap`は、CDKが使用するS3バケット、ECRリポジトリ、CloudFormation Execution Role等を作成します。環境（アカウント+リージョン）ごとに1回だけ実行すればOKです。

詳細は → **[Learning/06_権限管理編.md](Learning/06_権限管理編.md)** および **[init/README.md](init/README.md)**

### 5. config.jsonの設定値を編集

```json
{
  "account": null,
  "region": "ap-northeast-1",
  "cognito": {
    "user_pool_name": "user-pool-finance-common",
    "client_name": "client-finance-common",
    "ssm_prefix": "/Cognito"
  },
  "dashboard": {
    "domain_name": "dashboard.finance.h-akira.net",
    "acm_certificate_arn": "arn:aws:acm:us-east-1:XXXXXXXXXXXX:certificate/...",
    "s3_bucket_name": "s3-finance-dashboard-contents",
    "api_gateway": {
      "domain_name": "XXXXXXXXXX.execute-api.ap-northeast-1.amazonaws.com",
      "stage_name": "stage-01"
    },
    "codebuild": {
      "codestar_connection_arn": "arn:aws:codeconnections:...",
      "backend": {
        "project_name": "build-finance-dashboard-backend",
        "github_owner": "h-akira",
        "github_repo": "FinanceDashboardProject_Backend",
        "branch": "main"
      },
      "frontend": {
        "project_name": "build-finance-dashboard-frontend",
        "github_owner": "h-akira",
        "github_repo": "FinanceDashboardProject_Frontend",
        "branch": "main"
      }
    }
  }
}
```

## デプロイ

### 全スタックの確認

```bash
cdk ls
```

出力例:
```
FinanceCommonCognitoStack
FinanceDashboardCodeBuildBackendStack
FinanceDashboardCodeBuildFrontendStack
FinanceDashboardMainStack
```

### CloudFormationテンプレートの生成

```bash
cdk synth
```

### 個別スタックのデプロイ

```bash
# Cognitoスタック
AWS_PROFILE=finance cdk deploy FinanceCommonCognitoStack

# Dashboard Mainスタック
AWS_PROFILE=finance cdk deploy FinanceDashboardMainStack

# 全スタック一括デプロイ
AWS_PROFILE=finance cdk deploy --all
```

### スタックの削除

```bash
AWS_PROFILE=finance cdk destroy FinanceDashboardMainStack
AWS_PROFILE=finance cdk destroy FinanceCommonCognitoStack
```

## Terraform版との対応

| Terraform | CDK |
|-----------|-----|
| `FinanceProject_Infra/common/cognito` | `FinanceCommonCognitoStack` |
| `FinanceProject_Infra/dashboard/main` | `FinanceDashboardMainStack` |
| `FinanceProject_Infra/dashboard/codebuild_backend` | `FinanceDashboardCodeBuildBackendStack` |
| `FinanceProject_Infra/dashboard/codebuild_frontend` | `FinanceDashboardCodeBuildFrontendStack` |

## 主な機能

### FinanceCommonCognitoStack
- Cognito User Pool作成
- Cognito User Pool Client作成（シークレット付き）
- SSM Parameter Storeへの認証情報保存
- パスワードポリシー設定（最小8文字、大文字/小文字/数字/記号必須）
- トークン有効期限設定（Access/ID: 30分、Refresh: 5日）

### FinanceDashboardMainStack
- S3バケット作成（フロントエンド静的ファイル用）
- CloudFront Distribution作成
- Origin Access Control (OAC)設定
- カスタムドメイン設定（ACM証明書）
- API Gateway Originの設定（/accounts/*, /api/*）
- SPAルーティング対応（404→200 /index.html）

### FinanceDashboardCodeBuildBackendStack
- CodeBuildプロジェクト作成（Backend用）
- IAMロール作成（SAMデプロイに必要な権限）
- GitHub Webhookの設定（mainブランチPUSH時に自動ビルド）
- Lambda、API Gateway、CloudFormation等の権限設定
- SSM Parameter Storeアクセス権限

### FinanceDashboardCodeBuildFrontendStack
- CodeBuildプロジェクト作成（Frontend用）
- IAMロール作成（S3デプロイに必要な権限）
- GitHub Webhookの設定（mainブランチPUSH時に自動ビルド）
- S3バケットへのデプロイ権限

## 権限管理

CDKでは、**CDK実行者**（開発者/CI/CD）と**CloudFormation Execution Role**の2つのロールが関与します。

### CDK実行者（開発者）に必要な権限

```json
{
  "必要な権限": [
    "cloudformation:* (スタック操作)",
    "s3:* (CDKアセットバケットのみ)",
    "iam:PassRole (CloudFormation Execution Roleのみ)"
  ],
  "不要な権限": [
    "lambda:CreateFunction",
    "s3:CreateBucket (アプリのバケット)",
    "cognito-idp:*"
  ]
}
```

**重要**: CDK実行者には、リソース作成権限は不要です。実際のリソース作成は、`cdk bootstrap`で作成されるCloudFormation Execution Roleが行います。

詳細は → **[Learning/06_権限管理編.md](Learning/06_権限管理編.md)**

---

## 注意事項

1. **client_secret**: Cognito Client SecretはCDKで自動的にSSMパラメータに保存されます。

2. **削除保護**: Cognito User PoolはRemovalPolicy.RETAINに設定されているため、`cdk destroy`でも削除されません。手動削除が必要です。

3. **ACM証明書**: 事前にus-east-1リージョンで証明書を作成しておく必要があります。

4. **Route53**: DNSレコード設定は含まれていません。手動で設定してください。

5. **CloudFormation Execution Role**: デフォルトではAdministratorAccess相当の権限が付与されます。本番環境では必ず`--cloudformation-execution-policies`でカスタムポリシー（[init/cfn-execution-policies.yaml](init/cfn-execution-policies.yaml)）を使用してください。

6. **API Gateway URL**: Dashboard MainスタックはSAMスタックからAPI Gateway URLを自動的にインポートします。`config.json`で`sam_stack_name`を指定する必要があります（詳細は「API Gateway URL の設定方法」参照）。

## 有用なコマンド

* `cdk ls`          - スタック一覧表示
* `cdk synth`       - CloudFormationテンプレート生成
* `cdk deploy`      - スタックデプロイ
* `cdk diff`        - デプロイ済みスタックとの差分表示
* `cdk destroy`     - スタック削除
* `cdk docs`        - CDKドキュメントを開く

## API Gateway URL の設定方法

Dashboard MainスタックはCloudFrontのOriginとしてAPI Gatewayを使用します。API Gateway URLは**SAMスタックから自動的にインポート**されます。

`config.json`で`sam_stack_name`を指定してください：

```json
{
  "dashboard": {
    "sam_stack_name": "finance-dashboard-backend-sam",
    ...
  }
}
```

**前提条件**:
- SAMスタック（Backend）が先にデプロイされていること
- SAMテンプレートのOutputにExportが設定されていること（下記参照）

**SAMテンプレート（template.yaml）の設定**:
```yaml
Outputs:
  FinanceDashboardApiUrl:
    Description: API Gateway endpoint URL for stage-01 for Finance Dashboard Backend
    Value: !Sub "https://${MainAPIGateway}.execute-api.${AWS::Region}.amazonaws.com/stage-01/"
    Export:
      Name: !Sub "${AWS::StackName}-ApiUrl"
```

CDKはSAMスタックの`${StackName}-ApiUrl`というExport値を`Fn::ImportValue`で参照し、URLからドメイン名とステージ名を自動的に抽出してCloudFrontのOriginに設定します。

---

## デプロイ順序の推奨

Terraform版と同様の依存関係を考慮した推奨デプロイ順序：

1. **Cognito** → 認証基盤（必須）
2. **CodeBuild Backend** → SAMでAPI Gatewayを作成
3. **Backend（SAM）をCodeBuildでデプロイ** → API Gatewayが作成される
4. **Dashboard Main** → S3 + CloudFront（SAMスタックからAPI Gateway URLを自動取得）
5. **CodeBuild Frontend** → S3バケットへのデプロイ（Mainスタック後）

```bash
# 1. Cognito
AWS_PROFILE=finance cdk deploy FinanceCommonCognitoStack

# 2. CodeBuild Backend
AWS_PROFILE=finance cdk deploy FinanceDashboardCodeBuildBackendStack

# 3. CodeBuildで Backend（SAM）をデプロイ（手動またはGitHub Push）
aws codebuild start-build --project-name build-finance-dashboard-backend --region ap-northeast-1

# 4. Dashboard Main（SAMスタックからAPI Gateway URLを自動インポート）
AWS_PROFILE=finance cdk deploy FinanceDashboardMainStack

# 5. CodeBuild Frontend
AWS_PROFILE=finance cdk deploy FinanceDashboardCodeBuildFrontendStack
```

## 改善点

Terraform版と比較したCDK版の改善点：

- **型安全性**: Pythonの型ヒントにより、設定ミスを事前に検出
- **依存関係管理**: `add_dependency()`で明示的な依存関係設定
- **コード再利用**: Constructパターンで共通ロジックを再利用可能
- **統合開発体験**: CDK CLIによる統一されたデプロイ体験

## 今後の拡張予定

- [ ] Custom Resource for Cognito Client Secret自動取得
- [ ] CloudWatch Alarms追加
- [ ] Lambda@Edge for CloudFront
- [ ] WAF統合
