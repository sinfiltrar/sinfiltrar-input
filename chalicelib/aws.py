import boto3

# S3 init
bucket_name = 'sinfiltrar-attachments'
AWS_INPUT_BUCKET_NAME = 'sinfiltrar-input'
bucket_location = 'https://sinfiltrar-attachments.s3-us-west-2.amazonaws.com'


s3 = boto3.resource('s3', )
s3client = boto3.client('s3')


# RDS init
DB_ENDPOINT="sinfiltrar.c2yrjc7heqtk.us-west-2.rds.amazonaws.com"
DB_PORT="5432"
DB_USER="postgres"
DB_REGION="us-west-2"
DB_NAME="sinfiltrar"

dbSession = boto3.Session()
rdsClient = boto3.client('rds')
token = rdsClient.generate_db_auth_token(DBHostname=DB_ENDPOINT, Port=DB_PORT, DBUsername=DB_USER, Region=DB_REGION)
