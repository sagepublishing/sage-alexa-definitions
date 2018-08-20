"""
SAGE Alexa skill for research method definitions 
"""

from __future__ import print_function
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import decimal


# --------------- Initialisation code / separated from lambda invocation  -----------------

class DataStore:
    dynamo_conn   = boto3.resource('dynamodb', region_name='us-east-1')
    synonym_table = dynamo_conn.Table('SageSynonyms')
    term_table    = dynamo_conn.Table('SageTerms')

# --------------- Levenstein function -------------------------
# Implementation courtesy of Wikibooks:
# https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]




# --------------- Helpers that build all of the JSON responses ----------------------

def build_error_response(output):
    return build_speechlet_response("Research Methods", output, "", True)

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "Research Methods: " + title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Data store access functions ----------------------------------

# DynamoDB reference = arn:aws:dynamodb:us-east-1:744526292976:table/SageTerms

def query_synonym(term):
    
    print( "Querying the data store for synonym: '{}'".format(term) )
    
    synonym_response = DataStore.synonym_table.query(
        KeyConditionExpression=Key('Synonym').eq(term)
    )

    if synonym_response['Count'] > 0:
        return synonym_response['Items'][0]['TermID']
    else:
        return None

def query_term(term_id):
    
    print( "Querying the data store for term: '{}'".format(term_id) )

    term_response = DataStore.term_table.query(
        KeyConditionExpression=Key('TermID').eq(term_id)
    )

    if term_response['Count'] > 0:
        return term_response['Items'][0]
    else:
        return None


# ----------------- Functions for formulating the spoken responses -----------------

def compose_presentation_phrase(term, pref_term):
    
    lev = levenshtein(term, pref_term)
    
    if pref_term != term and lev > 1:
        return "{} (typically known as {})".format(term, pref_term)
    else: 
        return "{}".format(pref_term)

def compose_sage_definition(spoken_term, resolved_term, term_id, term_def):

    pref_term  = term_def['PreferredTerm']
    definition = term_def['Definition']

    prefix_text = compose_presentation_phrase(spoken_term, pref_term)
    
    # Compose the definition response
    return "{0}: {1}".format(prefix_text, definition)

def compose_sage_narrower_terms(spoken_term, resolved_term, term_id, term_def):

    narrower_terms = []
    
    if 'NarrowerTerms' not in term_def:
        return "Sorry, it isn't possible to decompose '{}' any further".format(spoken_term)
    
    for narrower_term_id in term_def['NarrowerTerms']:
        narrow_response = DataStore.term_table.query(
            KeyConditionExpression=Key('TermID').eq(narrower_term_id),
            ProjectionExpression="PreferredTerm"
        )
        
        if narrow_response['Count'] > 0:
            narrower_terms.append(narrow_response['Items'][0]['PreferredTerm'])

    if len(narrower_terms) < 1:
        print("Error: NarrowerTerms element found, but no narrower terms extracted - fail gracefully")
        return "I'm sorry, the term '{}' can't be broken down any further".format(spoken_term)

    prefix_text = compose_presentation_phrase(spoken_term, term_def['PreferredTerm'])
    count_text  = "item" if len(narrower_terms) == 1 else "{0} items".format(len(narrower_terms))
    topics_text = ", ".join(narrower_terms)
        
    return "{0} can be broken down into the following {1}: {2}".format(prefix_text, count_text, topics_text)

def compose_sage_related_terms(spoken_term, resolved_term, term_id, term_def):

    related_terms = []
    
    if 'RelatedTerms' not in term_def:
        return "Sorry, the term '{}' isn't related to any other terms".format(spoken_term)
    
    for related_term_id in term_def['RelatedTerms']:
        related_response = DataStore.term_table.query(
            KeyConditionExpression=Key('TermID').eq(related_term_id),
            ProjectionExpression="PreferredTerm"
        )
        
        if related_response['Count'] > 0:
            related_terms.append(related_response['Items'][0]['PreferredTerm'])

    if len(related_terms) < 1:
        print("Error: RelatedTerms element found, but no related terms extracted - fail gracefully")
        return "I'm sorry, the term '{}' isn't related to any other terms in my database".format(spoken_term)

    prefix_text = compose_presentation_phrase(spoken_term, term_def['PreferredTerm'])
    count_text  = "item" if len(related_terms) == 1 else "{0} items".format(len(related_terms))
    topics_text = ", ".join(related_terms)
        
    return "{0} is related to the following {1}: {2}".format(prefix_text, count_text, topics_text)





# -------- Functions that parse the request and control the skill's behavior -----------

def handle_help_request(card_title, intro_text, short):

    session_attributes = {}
    
    short_help_text = "Try saying something like 'Ask Sage to define Econometrics'."
    
    long_help_text = "I can provide definitions, lower-level terms, and relatives " \
                     "for Research Methods. Try saying " \
                     "'Ask Sage to define Econometrics, " \
                     "'Ask Sage to decompose Statistical Inference', or " \
                     "'Ask Sage what Induction is related to'."

    speech_output = intro_text + " "
    speech_output += short_help_text if short else long_help_text
                    
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = short_help_text
                    
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def find_resolved_term(intent):

    # Retrieve the resolved term, gracefully handling any issues with missing data

    term = intent['slots'].get('Term', None)
    if term == None:
        return None 
    
    resolutions = term.get('resolutions', None)
    if resolutions == None:
        return None
    
    resolutions_per_auth = resolutions.get('resolutionsPerAuthority')
    if resolutions_per_auth == None or len(resolutions_per_auth) < 1:
        return None
    
    res_values = resolutions_per_auth[0].get('values', None)
    if res_values == None or len(res_values) < 1:
        return None 

    return res_values[0]['value']['name']



    

def handle_sage_request(intent_name, intent, session):
    
    
    if 'Term' not in intent['slots']:
        print("Error: No Term detected in input message")
        return build_response(session_attributes, build_error_response(
            "I'm sorry, I couldn't find a Research Method term in that sentence"))

    spoken_term   = intent['slots']['Term']['value']
    resolved_term = find_resolved_term(intent) 
    
    if resolved_term == None:
        print("Alexa failed to resolve spoken term '{}'".format(spoken_term))
        return build_response(session_attributes, build_error_response(
            "I'm sorry, I wasn't able to find a term named '{}'".format(spoken_term)))
        
    print("Alexa resolved spoken term '{}' to SRM entity '{}'".format(spoken_term, resolved_term))
    
    term_id = query_synonym(resolved_term)
    if term_id == None: 
        print("Unable to find ID for resolved term '{}' - Potential DB / Alexa skill inconsistency?".format(resolved_term))
        return build_response(session_attributes, build_error_response(
            "I'm sorry, but there was a problem matching '{}' to my list of Research Method names".format(spoken_term)))

    term_def = query_term(term_id)
    if term_def == None:
        print("Unable to find definition for resolved term '{}:{}' - Potential DB / Alexa skill inconsistency?".format(term_id, resolved_term))
        return build_response(session_attributes, build_error_response(
            "I'm sorry, that's a valid term but there was a problem finding a matching definition"))        
    
    # Dispatch the spoken term and resolved term for data retrieval processing
    if intent_name == "SageDefineIntent":
        speech_output = compose_sage_definition(spoken_term, resolved_term, term_id, term_def)
    elif intent_name == "SageDecomposeIntent":
        speech_output = compose_sage_narrower_terms(spoken_term, resolved_term, term_id, term_def)
    elif intent_name == "SageRelatedIntent":
        speech_output = compose_sage_related_terms(spoken_term, resolved_term, term_id, term_def)

    card_title = resolved_term
    session_attributes = {}
    reprompt_text = None
    should_end_session = True

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    
    card_title = "Session Ended"
    speech_output = "Thank you for interacting with SAGE Research Methods Definitions, have a nice day. "
    
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))



# --------------- Event handlers ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts. Add any session initialisation here """

    print("on_session_started requestId=" 
            + session_started_request['requestId']
            + ", sessionId=" + session['sessionId'])

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they want """

    print("on_launch requestId=" 
            + launch_request['requestId'] 
            + ", sessionId=" + session['sessionId'])
          
    # Dispatch to your skill's launch function
    return handle_help_request("Welcome","Welcome to SAGE Research Methods Definitions.", False)

def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" 
            + intent_request['requestId'] 
            + ", sessionId=" + session['sessionId'])

    # Comment in the following line to log the request 
    #print("on_intent request={}".format(intent_request))

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "SageDefineIntent":
        return handle_sage_request("SageDefineIntent", intent, session)
    elif intent_name == "SageDecomposeIntent":
        return handle_sage_request("SageDecomposeIntent", intent, session)
    elif intent_name == "SageRelatedIntent":
        return handle_sage_request("SageRelatedIntent", intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return handle_help_request("Help","", False)
    elif intent_name == "AMAZON.FallbackIntent":
        return handle_help_request("Sorry?","I'm sorry, I don't know how to process that request.", True)
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    
    print("on_session_ended requestId=" 
          + session_ended_request['requestId'] 
          + ", sessionId=" + session['sessionId'])
          
    # Add any cleanup logic here

# --------------- Main request handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    # Reject any request unless it originates from the Alexa skill
    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.dd09e1de-f731-4f1c-8864-546f3ab1b18e"):
        raise ValueError("Invalid Application ID")

    # Detect if this is a new session, and perform any initialisation 
    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']}, event['session'])

    # Handle the request
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

