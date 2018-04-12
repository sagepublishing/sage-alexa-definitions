# sage-alexa-definitions

# Development

## Technical Design Summary

SKOS data
Data loading script
AWS developer console (Alexa skill)
Lambda
DynamoDB
AWS security

## Loading Sage Research Method definitions into DynamoDB

1. Obtain AWS credentials
2. Set up your environment (aws_cli, python3)
3. Extract the SRM definitions in skos format
4. Download the Alexa skill definition json
5. Run the script
```./skos_def_processor.py SRMont-2018-01-01.skos alexa_skill_def.xml```
This overwrites existing definitions, adds new. 
Nothing is cleared
6. Load new alexa skill definition json
7. Build the skill

## How to access the database 

URL for querying - fairly self explanitory UI
Dynamo DB data model

# Deployment and Usage

## How to add users to the Beta

## Going live

## Using the Skill

alexa, ask sage to define [term]
alexa, ask sage to decompose [term]

Fuzzy matching (skepticism)
"typically known as" (psychometrics vs psychological tests)


## Finding user queries in the logs

1. Log in to AWS CloudWatch
2. Access the sageDefineTerms log group, click Search Log Group. 
[Shortcut link](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logEventViewer:group=/aws/lambda/sageDefineTerms)
3. Enter "Alexa resolved"
4. Enter "Alexa failed" 


