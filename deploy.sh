# OUTPUT=`chalice deploy --connection-timeout 6000 --no-autogen-policy`
# OUTPUT=`cat deploy.output`

HOSTED_ZONE=`echo "$OUTPUT" | awk '/HostedZoneId: ([0-9A-Z]+)/ { print $2 }'`
DOMAIN_NAME=`echo "$OUTPUT" | awk '/AliasDomainName: (.+)/ { print $2 }'`

HOSTED_ZONE=Z2OJLYMUO9EFXC
DOMAIN_NAME=d-1nyi77bm80.execute-api.us-west-2.amazonaws.com


echo $HOSTED_ZONE
echo $DOMAIN_NAME

aws route53 change-resource-record-sets --hosted-zone-id Z0832787YMKJ27WDQ5UT --change-batch \
'{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.sinfiltr.ar",
        "Type": "A",
        "AliasTarget": {
          "DNSName": "'"$DOMAIN_NAME"'",
          "HostedZoneId": "'"$HOSTED_ZONE"'",
          "EvaluateTargetHealth": false
        }
      }
    }
  ]
}'

# FIXME: not safe!! sql like injection possible
