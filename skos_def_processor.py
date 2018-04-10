#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import xml.etree.ElementTree as ET
import boto3
import simplejson as json

terms     = {}
synonyms  = {}
hierarchy = {}


def main(skos_xml_file):

	# Set up XML parsing
	ns = {'rdf' : 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'skos': 'http://www.w3.org/2004/02/skos/core#'}  

	tree = ET.parse(skos_xml_file)
	root = tree.getroot()

	alexa_skill_data = []

	# Process the XML
	for sage_term_el in root.findall('rdf:Description',ns):

			# Obtain the Term ID
			# Employs a workaround for python's poor XML namespace support for attributes
			term_attrib_key = "{"+ns['rdf']+"}about" 
			term_id = sage_term_el.get(term_attrib_key)

			# Use the first preferred label and definition elements that are found
			pref_label = sage_term_el.find('skos:prefLabel',ns).text.lower()
			definition = sage_term_el.find('skos:definition',ns).text

			# Store the term in readiness for DynamoDB, and for the Alexa skill config
			terms[term_id] = {
				'TermID' : term_id,
				'PreferredTerm' : pref_label,
				'Definition' : definition
			}

			alexa_slot_value = {
				"name": {
					"id" : term_id,
					"value" : pref_label,
					"synonyms": []
        }
			}


			# Retrieve broader terms / hierarchy
			for broader_el in sage_term_el.findall('skos:broader',ns):
				rdf_resource_key = "{"+ns['rdf']+"}resource"
				broader_term_id = broader_el.get(rdf_resource_key)

				hierarchy_set = hierarchy.get(broader_term_id, set())
				hierarchy_set.add(term_id)
				hierarchy[broader_term_id] = hierarchy_set

			# Obtain all possible alternative labels i.e. synonyms
			synonyms[pref_label] = term_id

			for alt_label_el in sage_term_el.findall('skos:altLabel',ns):
				synonym = alt_label_el.text.lower()
				synonyms[synonym] = term_id
				alexa_slot_value['name']['synonyms'].append(synonym)

			# Record the alexa skill slot data, for later writing
			alexa_skill_data.append(alexa_slot_value)


	# Set up database access
	dynamodb = boto3.resource('dynamodb')
			
	sage_terms    = dynamodb.Table('SageTerms')
	sage_synonyms = dynamodb.Table('SageSynonyms')

	term_batch = sage_terms.batch_writer()
	syn_batch  = sage_synonyms.batch_writer()

	# Write all the terms
	for term_id in terms:
		print("Writing term {}".format(term_id))

		term = terms[term_id]
		if term_id in hierarchy:
			term['NarrowerTerms'] = hierarchy.get(term_id)

		### Comment me in to actually write to dynamo
		# term_batch.put_item(
		# 	Item=term
		# )			

	# Write all the synonyms
	for syn in synonyms:
		print("Writing synonym {}".format(syn))
		### Comment me in to actually write to dynamo
		# syn_batch.put_item(
		# 	Item={
		# 	'Synonym': syn,
		# 	'TermID': synonyms[syn]
		# 	}
		# )

	# Write the alexa skill slot data values to disk
	with open("alexa_slot_values.json", "w") as json_file:
		json_file.write(json.dumps(alexa_skill_data, sort_keys=True, indent=4 * ' '))




if __name__ == "__main__":
	main(sys.argv[1])


