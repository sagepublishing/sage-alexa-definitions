"""
SAGE Alexa skill for research method definitions 
"""

from __future__ import print_function
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import decimal


# --------------- Initialisation code / separated from lambda invocation  -----------------

dynamodb      = boto3.resource('dynamodb', region_name='us-east-1')
synonym_table = dynamodb.Table('SageSynonyms')
term_table    = dynamodb.Table('SageTerms')

# --------------- Levenstein function -------------------------
# Implementation courtest of Wikibooks:
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

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
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
    
    synonym_response = synonym_table.query(
        KeyConditionExpression=Key('Synonym').eq(term)
    )

    if synonym_response['Count'] > 0:
        return synonym_response['Items'][0]['TermID']
    else:
        return None

def query_term(term_id):
    
    print( "Querying the data store for term: '{}'".format(term_id) )

    term_response = term_table.query(
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
        return "{}, typically known as {}".format(term, pref_term)
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
        narrow_response = term_table.query(
            KeyConditionExpression=Key('TermID').eq(narrower_term_id),
            ProjectionExpression="PreferredTerm"
        )
        
        if narrow_response['Count'] > 0:
            narrower_terms.append(narrow_response['Items'][0]['PreferredTerm'])

    prefix_text = compose_presentation_phrase(spoken_term, term_def['PreferredTerm'])
    topics_text = ", ".join(narrower_terms)
        
    return "{0} can be broken down into the following {1} items: {2}".format(prefix_text, len(narrower_terms), topics_text)

def compose_sage_related_terms(spoken_term, resolved_term, term_id, term_def):

    related_terms = []
    
    if 'RelatedTerms' not in term_def:
        return "Sorry, the term '{}' isn't related to any other terms".format(spoken_term)
    
    for related_term_id in term_def['RelatedTerms']:
        related_response = term_table.query(
            KeyConditionExpression=Key('TermID').eq(related_term_id),
            ProjectionExpression="PreferredTerm"
        )
        
        if related_response['Count'] > 0:
            related_terms.append(related_response['Items'][0]['PreferredTerm'])

    prefix_text = compose_presentation_phrase(spoken_term, term_def['PreferredTerm'])
    topics_text = ", ".join(related_terms)
        
    return "{0} is related to the following {1} items: {2}".format(prefix_text, len(related_terms), topics_text)





# -------- Functions that parse the request and control the skill's behavior -----------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the SAGE 'define terms' skill. " \
                    "Please ask me which term you want to have defined by saying something like, " \
                    "SAGE define hypothesis"
                    
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please ask me to define a term by saying something like, " \
                    "SAGE define hypothesis."
                    
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
    
    session_attributes = {}
    reprompt_text = None
    
    if 'Term' in intent['slots']:
        
        spoken_term   = intent['slots']['Term']['value']
        resolved_term = find_resolved_term(intent) 
        
        if resolved_term != None:
            
            print("Alexa resolved spoken term '{}' to SRM entity '{}'".format(spoken_term, resolved_term))
            
            term_id = query_synonym(resolved_term)
            if term_id == None: 
                # This is an error, likely caused by inconsistency between the Alexa skill definition and DynamoDB
                return "I'm sorry, but there was a problem matching '{}' to my list of Research Method names".format(spoken_term)
        
            term_def = query_term(term_id)
            if term_def == None:
                # This is an error, likely caused by inconsistency between the Alexa skill definition and DynamoDB
                return "I'm sorry, that's a valid term but there was a problem finding a matching definition"
            
            # Dispatch the spoken term and resolved term for data retrieval processing
            if intent_name == "SageDefineIntent":
                speech_output = compose_sage_definition(spoken_term, resolved_term, term_id, term_def)
            elif intent_name == "SageDecomposeIntent":
                speech_output = compose_sage_narrower_terms(spoken_term, resolved_term, term_id, term_def)
            elif intent_name == "SageRelatedIntent":
                speech_output = compose_sage_related_terms(spoken_term, resolved_term, term_id, term_def)

        else:
            print("Alexa failed to resolve spoken term '{}'".format(spoken_term))
            
            speech_output = "I'm sorry, I wasn't able to find a term named '{}'".format(spoken_term)
            
    else:
        speech_output = "I'm sorry, I couldn't find a Research Method term in that sentence"
        
    should_end_session = True

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    
    card_title = "Session Ended"
    speech_output = "Thank you for interacting with SAGE, have a nice day. "
    
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))



# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
          
    # add any cleanup logic here

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they want """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
          
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    # Comment in the following line to log the request
    print("on_intent request={}".format(intent_request))

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
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
