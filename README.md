# sinfiltrar-input

Chalice project for AWS Lambda. Pushes SES input to PostrgreSQL.

## Getting Started

```
source venv/bin/activate
```

## Connect to the database

You must have a valid AWS config with valid permissions. Then run:

```
./dbconn.sh
```

## Deploy to AWS Lambda

You must have a valid AWS config with valid permissions. Then run, right from your virtual env path:

```
chalice deploy
```

