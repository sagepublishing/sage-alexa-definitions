# sage-alexa-definitions

# Development

## Technical Design

The SAGE Research Methods (SRM) skill has the following components:

* _Alexa skill definition (Amazon Developer Console / json)_: describes the Alexa skill to Amazon in terms of acceptance utterances, recognisable terms, synonyms, etc. 
* _DynamoDB (Amazon Web Services)_: stores terms, synonyms, definitions, and relationships for use in the skill.
* _Data loading script (Python)_: takes a SKOS file of SRM terms and synonyms, and loads them into an AWS data store. Also generates the Alexa skill definition.
* _Lambda script (AWS / Python)_: provides a service that the Alexa skill uses to retrieve spoken responses to user queries. The lambda retrieves term definitions (etc) from DynamoDB, then returns English sentences for Alexa to read out.
* _Alexa skill configuration (Amazon Developer Console)_: Configuration for skill beta testing and deployment, plus various other skill configuration is fully embedded into the Amazon Developer Console.

Note that the data loading script should be run locally, while everything else is hosted in the Cloud. 

## Accessing AWS / cloud resources

1. Obtain AWS credentials

You will need an username and password for the following AWS account: 7445-2629-2976

Make sure you have all of the following, for your user:

* User name
* Password
* Access key ID
* Secret access key

You'll need these to access the Amazon console, and to run access AWS from your local environement.

2. Create an Amazon developer account (optional) 

The Alexa skill needs to be owned by a single [Amazon developer account](https://developer.amazon.com/). The version recently demoed is owned by Alan Maloney, so the skill definition can only currently be modified by him. 

To independently deploy the skill, you will need your own Amazon developer account.

## Loading Sage Research Method definitions into DynamoDB

**1. Install Python**

The data loading script requires Python 3 to be installed on your local machine. The following resources provide installation instructions:

[Python on Windows](https://docs.python.org/3/using/windows.html)
[Python on Mac](https://docs.python.org/3/using/mac.html)

Note that Python version 3 executables typically include the number '3', e.g. python3, pip3.

**2. Install required python packages**

The data loading script requires the following Python packages, all of which can be installed with the Python's built-in package manager:

* awscli
* simplejson

To install a package, use the command `'pip3 install {packagename}'`. 

Note that the awscli package includes command line tools for working with AWS services (e.g. the `aws` command). You may need to modify your PATH environment variable to run these commands.

**3. Set up your environment**

Next, make sure that:

- the 'python3' executable is on your path
- the following environment variables have been set up:

```
AWS_ACCESS_KEY_ID={your access key ID}
AWS_SECRET_ACCESS_KEY={your secret access key}
AWS_DEFAULT_REGION=us-east-1
AWS_DEFAULT_OUTPUT=json
```

I recommend creating a small script to set these up for you. 

A unix-like template for such a file can be found in the file `env.sh`. It can be run using the unix `source` command which runs in the current environment, and retains any newly defined environment variables. 

**4. Extract the SRM definitions in skos format**

You will need a file of SRM definitions in the [SKOS](https://www.w3.org/2004/02/skos/) format, e.g.:

``` xml
  <rdf:Description rdf:about="SRM0100">
    <rdf:type rdf:resource="http://www.w3.org/2004/02/skos/core#Concept" />
    <skos:broader rdf:resource="SRM0057" />
    <skos:broader rdf:resource="SRM0101" />
    <skos:related rdf:resource="SRM0100" />
    <skos:related rdf:resource="SRM0427" />
    <skos:prefLabel xml:lang="en">Praxis</skos:prefLabel>
    <skos:definition xml:lang="en">A term with no precise equivalent in English, it refers to a form of human action concerned with what is right and good in a given situation, and the competence, sensibility, and sensitivity required to make such judgements.</skos:definition>
  </rdf:Description>
```

Alan Maloney is the maintainer of the master data definitions of SRM terms, and can export a complete set of definitions in SKOS format. 

**5. Download the Alexa skill definition json**

Before running the script, you will need a copy of the currently deployed Alexa skill definition, in JSON format. This can be downloaded from the Amazon Developer Console.

The relevant console page for the Demo Alexa app (owned by Alan Maloney) can be found [here](https://developer.amazon.com/alexa/console/ask/build/custom/amzn1.ask.skill.d92b89ac-f809-447c-8c29-556976594ff6/development/en_GB/json-editor).

Select all the JSON in JSON Editor, then save this text to file on your local machine. 

**_Make sure you download the latest Alexa skill definition, rather than using an a version you downloaded previously!_**  



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


