#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import lxml.html
import scraperwiki
import random
import codecs
from Queue import Queue
from datetime import datetime
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import os
import argparse

dateScraped = datetime.strftime(datetime.now(), '%Y-%m-%d')

parser = argparse.ArgumentParser()
parser.add_argument("domain", help="The domain you want to monitor")
parser.add_argument("--firstrun", help="If set will generate initial database, otherwise will check for new and modified documents", dest='firstrun', action='store_true')
parser.add_argument("--verbose", help="makes it more verbose, obvs", dest='verbose', action='store_true')
args = parser.parse_args()

domain = args.domain
testing = False
firstRun = args.firstrun
newDocs = False
updatedDocs = False
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
	global visited, tovisit, totalRequests, erroredRequests,updatedDocs,newDocs
	if url not in visited:
		if verbose:
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
						scraperwiki.sqlite.save(unique_keys=["url"], data=data, table_name="allDocuments")

				elif firstRun == False:
					queryString = u"* from allDocuments where url='{url}'".format(url=url)
					queryResult = scraperwiki.sqlite.select(queryString)

					# it hasn't been scraped before

					if not queryResult:
						print "new data, saving", data['url'].encode('utf-8')
						newDocs = True
						if not testing:
							scraperwiki.sqlite.save(unique_keys=["url"], data=data, table_name="allDocuments")
							scraperwiki.sqlite.save(unique_keys=["url","dateScraped"], data=data, table_name="newDocuments")

					# if it has been saved before, check if it has been updated

					else:
						if data['contentLength'] != queryResult[0]['contentLength']:

							# it has been updated, so save the new values in the main database table and the updates table
							updatedDocs = True
							print data['url'].encode('utf-8'), "has been updated"
							if not testing:
								scraperwiki.sqlite.save(unique_keys=["url"], data=data, table_name="allDocuments")
								scraperwiki.sqlite.save(unique_keys=["url","dateScraped","contentLength"], data=data, table_name="updatedDocuments")

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
			print "error on getting", url.encode('utf-8')
			print e
			erroredRequests+=1
			if erroredRequests > 20:
				print "their website is probs down, hey"

# Start with the homepage

tovisit.put(domain)

print "Running..."

while not tovisit.empty() and erroredRequests <= 20:
	scrapePage(tovisit.get())
	tovisit.task_done()

print "Done, checked {totalRequests} URLs".format(totalRequests=totalRequests)


if newDocs:
	queryString = "* from newDocuments where dateScraped='{dateScraped}'".format(dateScraped=dateScraped)
	allNewDocs = scraperwiki.sqlite.select(queryString)
	print len(allNewDocs)," new documents"

if updatedDocs:
	queryString = "* from updatedDocuments where dateScraped='{dateScraped}'".format(dateScraped=dateScraped)
	allUpdatedDocs = scraperwiki.sqlite.select(queryString)
	print len(allUpdatedDocs)," updated documents"

# email notifications to go here

EMAIL_ALERT_PASSWORD = os.environ['EMAIL_ALERT_PASSWORD']

fromaddr = "alerts@nickevershed.com"
toaddr = "nick.evershed@theguardian.com"
 
msg = MIMEMultipart()
 
msg['From'] = fromaddr
msg['To'] = toaddr

if not newDocs and not updatedDocs:
	msg['Subject'] = "Report checker run, no new or updated documents"
	body = "Done, checked {totalRequests} URLs".format(totalRequests=totalRequests)

elif newDocs or updatedDocs:
	msg['Subject'] = "Report checker run, there are new or updated documents"
	body = "{numberNewDocs} new documents and {numberUpdatedDocs} updated documents".format(numberNewDocs=len(allNewDocs), numberUpdatedDocs=len(numberUpdatedDocs))


msg.attach(MIMEText(body, 'plain'))
 
server = smtplib.SMTP_SSL('mail.nickevershed.com', 465)
server.login(fromaddr, EMAIL_ALERT_PASSWORD)
text = msg.as_string()
server.sendmail(fromaddr, toaddr, text)
server.quit()

print "Email sent"

