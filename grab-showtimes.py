# MAGIC COMMENT FOR PYTHON2 coding: utf-8
# grab-showtimes.py
# 2012 Viiksipojat / Mikko Leino
# 
# fetches current day's showtimes for movie theaters in helsinki 
# and produces a html page defined in index.mustache
#
# requirements: python 2.6 or 2.7,
#				pystache
#
# configuration: fill in your oma kaupunki api key to leffat.conf (http://api.omakaupunki.fi/)
#
# usage: python grab-showtimes.py output.html

import codecs
import datetime
import json
import pystache
import sys
import urllib
from email.utils import parsedate
from xml.dom.minidom import parseString

if len(sys.argv) < 2:
	print("usage: python {0} output.html".format(sys.argv[0]))
	sys.exit(1)

config = {}
execfile(sys.path[0] + "/leffat.conf", {}, config)

DATA = { "showtimes": [] } # MASTER DATA COLLECTION
TEMPLATE = sys.path[0] + "/index.mustache"

# UTILITY ->

# timezone hack
# the script is deployed on EST (UTC-05), but we're interested in EET (UTC+02), so some fiddling is necessary
tzdelta = datetime.timedelta(0,0,0,0,0,7) # seven hours
now     = datetime.datetime.today()+tzdelta
today   = datetime.date(now.year, now.month, now.day) # datetime.date.today() in helsinki time

def zeropad(i): 
	"""Turns integer /i/ to a string padding a zero if /i/ < 10."""
	s = str(i)
	return s if len(s) > 1 else "0" + s

def finnkinoQueryDate(d):
	"""Returns a string representation in Finnkino query string format of Date object /d/."""
	return str(d.year) + "." + zeropad(d.month) + "." + zeropad(d.day)

def showtimeFromTimestring(timestring):
	"""Returns a '%H.%M' time string from a ISO 8601 date and time string."""
	d = datetime.datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S")
	return zeropad(d.hour) + "." + zeropad(d.minute)

def showtimeFromPOSIX(timestamp):
	"""Returns a '%H.%M' time string from a POSIX timestamp. NB! assumes EST and produces EET (time zone mangling in action)."""
	return (datetime.datetime.fromtimestamp(timestamp)+tzdelta).strftime("%H.%M")

def showtimeFromRFC2822(timestamp):
	"""Returns a '%H.%M' time string from a RFC 2822 timestamp."""
	return (datetime.datetime(*parsedate(timestamp)[0:6])).strftime("%H.%M")

def showtimeFromOK(timestring):
	"""Returns a '%H.%M' time string from a POSIX timestamp or RFC 2822 timestamp."""
	if "," in timestring:
		return showtimeFromRFC2822(timestring)
	else:
		return showtimeFromPOSIX(timestring)

def getFinnkinoTheater(t):
	"""Returns just the name of the theater from Finnkino supplied pile of random data."""
	if "Helsinki" in t:
		tt = t.split(", Helsinki, sali ")
	else:
		tt = t.split(", sali ")
	return tt[0]# + " " + tt[1]
# /UTILITY

# OMA KAUPUNKI ->
def omakaupunkiData(theater):
	"""Queries showtimes from Oma Kapunki API."""
	params = "?" + urllib.urlencode({
		"api_key": 		ok_apikey,
		"area": 		"helsinki", #sorry espoovantaa
		"category":		9,
		"start_date":	str(today),
		"end_date":		str(today),
		"text":			theater
	})
	response = urllib.urlopen(ok_apiroot + "/event/search" + params)
	jsondata = json.loads(response.read().decode('utf8'))
	if "data" in jsondata:
		return jsondata["data"]
	else:
		return None

ok_apikey  = config["OMAKAUPUNKI_APIKEY"]
ok_apiroot = "http://api.omakaupunki.fi/v1"
ok_theaters = ["orion", "kino+engel", "bio+rex", "kesäkino+engel"] 
# TODO: 
# - artova kino (not in oma kaupunki)
# - kino helios (?)
# - kino itäkeskus (?)
# - kino k-13 (?) =? ses auditoria (?)
# - kino tulio (?)
# - walhalla (?)
# FIXME:
# - kesäkino engel shows up twice because kino+engel is also substring of kesäkino+engel
for theater in ok_theaters:
	showdata = omakaupunkiData(theater)
	if showdata != None and len(showdata) != 0:
		for show in showdata:
			DATA["showtimes"].append( {
				"timelabel": 	showtimeFromOK(show["start_time"]),
				"title":     	show["title"],
				"theater":		theater.replace("+", " ").title(),
				"url":			show["url"]
			} )

# FINNKINO -> 
fk_apiroot = "http://www.finnkino.fi/xml/Schedule/?area=1002&dt=" + finnkinoQueryDate(today)
response = urllib.urlopen(fk_apiroot)
dom = parseString(response.read())
for node in dom.getElementsByTagName("Show"):
	DATA["showtimes"].append( {
		"timelabel": 	showtimeFromTimestring(node.getElementsByTagName("dttmShowStart")[0].childNodes[0].data),
		"title":		node.getElementsByTagName("Title")[0].childNodes[0].data,
		"theater": 		getFinnkinoTheater(node.getElementsByTagName("TheatreAndAuditorium")[0].childNodes[0].data),
		"url": 			node.getElementsByTagName("ShowURL")[0].childNodes[0].data
	} )

# preprocess DATA
DATA["showtimes"].sort(key=lambda showtime: (showtime["timelabel"], showtime["title"]))
lastTimelabel = ""
for showtime in DATA["showtimes"]:
	showtime["hour"]   			= showtime["timelabel"][:2]
	showtime["minute"] 			= showtime["timelabel"][3:]
	showtime["theaterclass"] 	= showtime["theater"].replace(" ", "-") 
	if showtime["timelabel"] == lastTimelabel:
		lastTimelabel = showtime["timelabel"]
		del showtime["timelabel"] 
	else:
		lastTimelabel = showtime["timelabel"]

renderer = pystache.Renderer(string_encoding="utf8", file_encoding="utf8")
template = codecs.open(TEMPLATE, "r", "utf_8").read()
output = codecs.open(sys.argv[1], "w", "utf_8")
output.write(renderer.render(template, DATA))
output.close()