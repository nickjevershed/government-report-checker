#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import lxml.html
import scraperwiki
import random
import codecs
from Queue import Queue
from datetime import datetime

dateScraped = datetime.strftime(datetime.now(), '%Y-%m-%d')
domain = "https://www.ag.gov.au"
testing = False
firstRun = True
tovisit = Queue()
visited = set()
totalRequests = 0
erroredRequests = 0
files = ['pdf','doc','docx','xls','xlxs','epub','rtf','txt','ppt','pptx','odt']

if testing:
	print "Testing mode, data won't be saved"

if firstRun:
	print "First run, generating initial database of documents"

def checkDocType(url):
	extension = url.split(".")[-1]
	if extension.lower() in files:
		return True
	else:
		return False	

def scrapePage(url):
	global visited, tovisit, totalRequests, erroredRequests
	if url not in visited:
		print "getting",url.encode('utf-8')
		visited.add(url)
		totalRequests+=1

		try:
			
			# Check if it's a doc, save it 

			if checkDocType(url):
				r = requests.head(url)
				if 'last-modified' in r.headers:
					lastModified = r.headers['last-modified']
				else:
					lastModified = ""

				if 'content-length' in r.headers:
					contentLength = r.headers['content-length']
				else:
					contentLength = ""

				data = {}
				data['fileName'] = url.split("/")[-1]
				data['url'] = url
				data['lastModified'] = lastModified
				data['dateScraped'] = dateScraped
				data['contentLength'] = contentLength

				if firstRun == True:
					if not testing:
						scraperwiki.sqlite.save(unique_keys=["url","lastModified"], data=data, table_name="allDocuments")

				elif firstRun == False:
					queryString = u"* from allDocuments where url='{url}'".format(url=url)
					queryResult = scraperwiki.sqlite.select(queryString)

					# it hasn't been scraped before

					if not queryResult:
						print "new data, saving"
						if not testing:
							scraperwiki.sqlite.save(unique_keys=["url","lastModified"], data=data, table_name="allDocuments")
							scraperwiki.sqlite.save(unique_keys=["url","lastModified","dateScraped"], data=data, table_name="newDocuments")

					# if it has been saved before, check if it has been updated

					else:
						if data['lastModified'] != queryResult[0]['lastModified']:

							# it has been updated, so save the new values in the main database table and the updates table

							print data['url'].encode('utf-8'), "has been updated"
							if not testing:
								scraperwiki.sqlite.save(unique_keys=["url","lastModified"], data=data, table_name="allDocuments")
								scraperwiki.sqlite.save(unique_keys=["url","lastModified","dateScraped"], data=data, table_name="updatedDocuments")

			# If not a doc, get the page and scrape the links into the queue	

			else:	
				r = requests.get(url)	
				dom = lxml.html.fromstring(r.content)
				linksOnPage = dom.cssselect("a")
				internalLinks = []

				for link in linksOnPage:
					if 'href' in link.attrib:
						href = link.attrib['href']
						
						if href.startswith('http') and domain in href:
							internalLinks.append(href)

						elif href.startswith('/'):	
							internalLinks.append(domain + href)

				for link in set(internalLinks):
					tovisit.put(link)

		except requests.exceptions.RequestException as e:
			print e
			erroredRequests+=1
			if erroredRequests > 20:
				print "their website is probs down, hey"

# Start with the homepage

tovisit.put(domain)

while not tovisit.empty() and erroredRequests <= 20:
	scrapePage(tovisit.get())
	tovisit.task_done()

# some sort of email notifications to go here

