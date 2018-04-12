# sage-alexa-definitions

# Development

## Technical Design Summary

Data loading script
AWS services

## Loading Sage Research Method definitions into DynamoDB

1. Obtain AWS credentials
2. Set up your environment
3. Extract the SRM definitions in skos format
4. Run the script
```./skos_def_processor.py SRMont-2018-01-01.skos```
This clears existing definitions
5. Create new alexa skill definition json
6. Upload alexa skill definition
7. Build the skill

## How to access the database 

Dynamo DB data model

# Deployment and Usage

## How to add users to the Beta

## Going live

## Using the Skill

## Finding user queries in the logs

1. Log in to AWS CloudWatch
2. Access the sageDefineTerms log group, click Search Log Group. 
[Shortcut link](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/sageDefineTerms)
3. Enter "Term unresolved"
4. Enter "Term resolved" 


