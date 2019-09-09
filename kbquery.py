#!/usr/bin/python
# -*- coding: UTF-8 -*-

import requests
import re
import string
import csv
import xml.etree.ElementTree as ET
from authliboclc import wskey
from authliboclc import user
import urllib2
import sys
import time

inputFile  = str(raw_input("Input File: "))
outputFile = str(raw_input("Name of file to save results: "))
queryType = str(raw_input('What are you searching on? ISSN, ISBN, OCN, or Title: '))
key = 'ahtH1Z7m1WW97DwsXtCekXe5EKqyyKwT0cikOdeVKhXcyofx6MKS3ISnzMrIFW4NxOKvZG1nF5mAnzuq'
lmKey = 'q83oyWx4xXLNytlXZA30EfYY7vC1nR3RuiBdcam7cKU6dRfIkljyicOtcVIUxIRZc3NyxozSjw7B1Hra'
secret = 'Ap5mhlKXxazHtgmkZLWEPF6imBB0CoQa'
principal_id = '7cd1d2ae-06fc-4172-9c91-cfb06f3d4e87'
principal_idns = 'urn:mace:oclc:idm:umaryland'
authenticating_institution_id = '1284'
ns = {'kb' : 'http://worldcat.org/kb', 'atom' : 'http://www.w3.org/2005/Atom', 'os' : 'http://a9.com/-/spec/opensearch/1.1/', 'df' : 'http://worldcat.org/xmlschemas/LicenseManager', 'gd' : 'http://schemas.google.com/g/2005'}
collectionID = str(raw_input("To search in a particular collection enter its ID. If you want to search a list of collections, type 'list'. Type 'no' otherwise: "))
fieldNames = ["publication_title", "print_identifier", "online_identifier", "date_first_issue_online", "num_first_vol_online", "num_first_issue_online", "date_last_issue_online", "num_last_vol_online", "num_last_issue_online", "title_url", "first_author", "title_id", "embargo_info", "coverage_depth",	"coverage_notes", "publisher_name", "location", "title_notes", "staff_notes", "vendor_id", "oclc_collection_name", "oclc_collection_id", "oclc_entry_id", "oclc_linkscheme", "oclc_number",	"ACTION"]
completeKbartCheck = 0
perAccess = ''
archivalCopy = ''

#ns variable is used for namespaces for the XML that the KB API returns

def perpetualAccessCheck(collUid):
	global perAccess
	global archivalCopy
	perAccess = ''
	archivalCopy = ''
#authentication code for License Manager API taken from OCLC documentation: https://github.com/OCLC-Developer-Network/oclc-auth-python
	request_url = 'https://1284.share.worldcat.org/license-manager/license/search?q=collectionId:' + collUid
	my_wskey = wskey.Wskey(
		key=lmKey,
		secret=secret,
		options=None
		)

	my_user = user.User(
		authenticating_institution_id=authenticating_institution_id,
		principal_id=principal_id,
		principal_idns=principal_idns
		)

	authorization_header = my_wskey.get_hmac_signature(
		method='GET',
		request_url=request_url,
		options={
		'user': my_user,
		'auth_params': None}
		)
	print (request_url)
	myRequest = urllib2.Request(
		url=request_url,
		data=None,
		headers={'Authorization': authorization_header}
		)
	time.sleep(1)
	r = urllib2.urlopen(myRequest).read()
	root = ET.fromstring(r)
	resultCheck = root.find('os:totalResults', ns)
	emptyCheck = resultCheck.text
	print('Results: ' + emptyCheck)
	if emptyCheck == "0":
		print('no license found')
		perAccess = 'no license found'
		archivalCopy = 'no license found'
		
	else:
		customTermPath = root.findall("atom:entry/atom:content/df:license/df:terms/df:term/[df:type='Custom Term']", ns)
		for match in customTermPath:
			namePath = match.findall("./df:name", ns)
			termValuePath = match.findall("./df:termValue", ns)
			for name in namePath:
				for termValue in termValuePath:
					if name.text == 'Perpetual Access Rights':
						if termValue.text == 'yes':
							perAccess = 'yes'
					else:
						perAccess = 'no or silent'
						#elif termValue.text == 'no':
						#	perAccess = 'no'
						#elif termValue.text == 'silent':
						#	perAccess = 'silent'
					#	elif termValue.txt is None:
						#	perAccess = 'silent'
		archivalCopyValue = root.find("atom:entry/atom:content/df:license/df:terms/df:term/[df:type='Archival_Copy_Provided']/df:termValue", ns)
		if archivalCopyValue is None:
			archivalCopy = 'silent'
		elif archivalCopyValue.text == 'yes':
			archivalCopy = 'yes'
		elif archivalCopyValue.text == 'no':
			archivalCopy = 'no'
		else:
			archivalCopy = 'silent'

if queryType == 'ISSN':
	searcher = 'issn='
elif queryType == 'ISBN':
	searcher = 'isbn='
elif queryType == 'Title':
	searcher = "title="
elif queryType == 'OCN':
	searcher = 'oclcnum='
else:
	searcher = 'q='

if collectionID == 'no':
	collectionSearch = ''
else:
	collectionSearch = "collection_uid="+collectionID

with open(inputFile, 'r') as f:
	with open(outputFile, 'a+') as o:
		o.write('number'+'	'+'status'+'	'+'title'+'	'+'ISBN or ISSN'+'	'+'ocn'+'	'+'Collection Name'+'	'+'KB ID'+'	' +'coverage'+'	'+'Perpetual Access'+'	'+'Archival Copy'+'	'+'Search Term'+'	'+'\n')
		termCount = 0
		for terms in f:
			if queryType == 'Title':
				term = '"'+terms.strip()+'"'
				if "&" in term:
					term = term.replace('&', '&amp;')
			else:
				term = terms.strip()
			termCount +=1
			print('Search number: ' +str(termCount)+'    Search term: '+term)
			if term == '\n' or term == '':
				o.write('blank'+'\n')
				print('no search term')
			else:
				url ='http://worldcat.org/webservices/kb/rest/entries/search?'+collectionSearch+'&'+searcher+term+'&wskey='+key
				print(url)
				r = requests.get(url.strip()).text
				results = r.encode('utf-8')
				root = ET.fromstring(results)
				resultCheck = root.find('os:totalResults', ns)
				emptyCheck = resultCheck.text
				if emptyCheck == "0":
					if collectionID == "no":
						o.write(term + ' not found' + '\n')
						print(term + ' not found')
					else:
						#if a collection ID is provided and a title is not found to be selected, this triggers the script to pull the full KBART
						#and then search to see if the title is not in the collection at all or simply not selected
						if completeKbartCheck == 0:
						#downloading complete KBART file
							collectionURL = 'http://worldcat.org/webservices/kb/rest/collections/'+collectionID+'?wskey='+key
							print(collectionURL)
							collectionResponse = requests.get(collectionURL.strip()).text
							collectionResults = collectionResponse.encode('utf-8')
							collectionResultsRoot = ET.fromstring(collectionResults)
							#Xpath may need to be fixed. Likely may need to do xpath just with attribute and value...?
							getLink = collectionResultsRoot.find('./atom:link[@title="kbart file"]', ns)
							link = getLink.get('href')
							kbartTitle = collectionID+'kbart.txt'
							fullLink = link + '?wskey='+key
							print(fullLink)
							print("downloading: " + kbartTitle)
							kbartRequest = requests.get(fullLink.strip()).text
							kbartRequest = kbartRequest.encode('utf-8')
							kbartTitle = collectionID+'kbart.txt'
							kbartWriter = open(kbartTitle, 'w+')
							kbartWriter.write(kbartRequest)
							kbartWriter.close()
						#ending complete KBART file download process and beginning to check the file
						completeKbartCheck += 1
						kbartData = open(kbartTitle, 'r')
						#after writing KBART data to a file, the script then reads the KBART and tries to find a match based on the kind of query, ISSN, OCN, etc
						tsvreader = csv.DictReader(kbartData, delimiter='\t')
						matchFound = 'no'
						for row in tsvreader:
							if queryType == 'ISSN':
								if term == row['online_identifier']:
									matchFound = 'yes'
								elif term == row['print_identifier']:
									matchFound = 'yes'
							elif queryType == 'ISBN':
								if term == row['online_identifier']:
									matchFound = 'yes'
								elif term == row['print_identifier']:
									matchFound = 'yes'
							elif queryType == 'Title':
								if term == row['publication_title']:
									matchFound = 'yes'
							elif queryType == 'OCN':
								if term == row["oclc_number"]:
									matchFound = 'yes'
							else:
								matchFound = 'no'
							numb = str(termCount)
							if matchFound == 'yes':
								break
						if matchFound == 'yes':
							o.write(numb+'\t'+'not selected but available in global KB'+'\t\t\t\t\t\t\t'+term+'\n')
							print(term + ' not selected')
						elif matchFound == 'no':
							o.write(numb+'\t'+'not available'+'\t\t\t\t\t\t\t'+term+'\n')
							print(term + ' not available')

				else:
					entryLoopNumber = 0
					for entry in root.findall('atom:entry', ns):
						entryLoopNumber +=1
						numb =str(termCount)+'.'+str(entryLoopNumber)
						titleText = entry.find('atom:title', ns)
						status = 'selected'
						if titleText is None:
							title = "No title"
						else:
							title = titleText.text
						ocnText = entry.find('kb:oclcnum', ns)
						if ocnText is None:
							ocn = "no OCN"
						else:
							ocn = ocnText.text
						covText = entry.find('kb:coverage', ns)
						if covText is None:
							cov = "no coverage"
						else:
							cov = covText.text
						coll = entry.find('kb:collection_name', ns).text
						issnCheck = entry.find('kb:issn', ns)
						if issnCheck is None:
							isbnCheck = entry.find('kb:isbn', ns)
							if isbnCheck is None:
								sn = "No Standard number found"
							else:
								sn = isbnCheck.text
						else:
							sn = issnCheck.text
						uidText = entry.find('kb:entry_uid', ns)
						if uidText is None:
							uid = "no KB ID"
						else:
							uid = uidText.text
						collUid = entry.find('kb:collection_uid', ns).text
						print('collUid = '+ collUid)
						perpetualAccessCheck(collUid)
						data = numb+'	'+status+'	'+title+'	'+sn+'	'+ocn+'	'+coll+'	'+uid+'	'+cov+'	'+perAccess+'	'+archivalCopy+'	'+term+'	'+'\n'
						data = data.encode('utf-8')
						print(data)
						o.write(data)
