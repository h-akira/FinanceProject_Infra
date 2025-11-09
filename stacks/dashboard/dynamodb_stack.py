from aws_cdk import (
  Stack,
  aws_dynamodb as dynamodb,
  RemovalPolicy,
  Tags,
)
from constructs import Construct

class DashboardDynamoDBStack(Stack):
  """
  DynamoDB Table for Finance Dashboard Backend
  """

  def __init__(
    self,
    scope: Construct,
    construct_id: str,
    table_name: str,
    environment: str,
    **kwargs
  ) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Create DynamoDB table
    table = dynamodb.Table(
      self, "DashboardTable",
      table_name=table_name,
      partition_key=dynamodb.Attribute(
        name="pk",
        type=dynamodb.AttributeType.STRING
      ),
      sort_key=dynamodb.Attribute(
        name="sk",
        type=dynamodb.AttributeType.STRING
      ),
      billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
      removal_policy=RemovalPolicy.RETAIN,
      point_in_time_recovery=True,
    )

    # Add tags
    Tags.of(self).add("Environment", environment)
    Tags.of(self).add("Created", "20251109")
    Tags.of(self).add("Name", "dashboard-dynamodb")

    # Output
    self.table = table
