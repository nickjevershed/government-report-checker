import requests
import lxml.html
import scraperwiki
import random
from Queue import Queue

domain = "https://www.ag.gov.au"

tovisit = Queue()
visited = set()
totalRequests = 0
erroredRequests = 0

def scrapePage(url):
	global visited, tovisit, totalRequests, errorRequests
	if url not in visited:
		print "getting",url
		visited.add(url)
		totalRequests+=1
		try:
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
			if erroredRequests > 5:
				print "their website is probs down, hey"

tovisit.put(domain)

while not tovisit.empty() and erroredRequests <= 5:
	scrapePage(tovisit.get())
	tovisit.task_done()

# scraperwiki.sqlite.save(unique_keys=["blah"], data=data)