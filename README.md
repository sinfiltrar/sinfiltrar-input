# sinfiltrar-input

Chalice project for AWS Lambda. Pushes SES input to PostrgreSQL.

## Getting Started

```
source venv/bin/activate
```

## Set .env file

Update as necesary

```
cp .env.example .env
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

## Running locally

```
chalice local --stage local
```

It's important to select the local stage so we set the appropiate CORS headers
and the local frontend can query from this instance.
