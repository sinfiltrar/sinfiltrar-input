# connect to DB

export DBHOST=sinfiltrar.c2yrjc7heqtk.us-west-2.rds.amazonaws.com
export DBPASS="$(aws rds generate-db-auth-token --hostname $DBHOST --port 5432 --region us-west-2 --username postgres )"
psql "host=$DBHOST port=5432 sslmode=verify-full sslrootcert=rds-combined-ca-bundle.pem dbname=sinfiltrar user=postgres password=$DBPASS"
