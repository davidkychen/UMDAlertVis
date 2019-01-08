import requests
import re
import googlemaps
import csv

#Years of interest and the urls that the application will be retrieving information from
YEAR = ["08","09","10","11","12","13","14","15","16"]
# url = "http://alert.umd.edu/alerts"
url = "http://www.umpd.umd.edu/stats/safety_notices_offcampus.cfm?year="
url_detail = "http://www.umpd.umd.edu/stats/"

#Googlemap API key(Deleted for pravicy)
gmaps = googlemaps.Client(key='')

#A global list that will store the clean data that are going to be written into the csv file
csvwrite = []

#Retrieve the location of the crime from the text using regular expression
def cleanLocation(text):
	# Search for something like 1234 york blvd
	temp = re.search(r'\d+([-\w\s]*)',text)
	result =""
	#If there is a match
	if temp:
		#Remove some unnecessary information in the text
		temp_text = re.sub(r' [Bb]l[ko][\S]* [o]*[f]*', " ",temp.group(0))
		temp_text = re.sub(r', College Park, MD',"",temp_text)
		result = temp_text
	#If there is no match
	else:
		#Search if there is something like xxx blvd/road...etc
		temp = re.search(r'[\w\s]+[@/atnd]+[\w\s]*[RoadBlvwPrkyDieA]+',text)
		if temp:
			#Remove unnecessary information
			temp_text = re.sub(r'([@/]|( and )|( at ))+'," & ",temp.group(0))
			temp_text = re.sub(r', College Park, MD',"",temp_text)
			result = temp_text
	result = result + ", College Park, MD"
	return(result)

#Send the cleaned location to GoogleMap API and return the result
def getGeoCode(client, location):
	try:
		geocode_result = client.geocode(location)
		return(geocode_result)
	except:
		print("Failed")

#Retrieve the date information from the text
def getDate(text):
	temp = re.search(r'top\">(.*)</td>',text)
	if temp:
		return(temp.group(1))

#Retrieve the URL from the text
def getUrl(text):
	temp = re.search(r'<td><a href=\"(.*)\">', text)
	if temp:
		return(temp.group(1))

#Retrieve the time the crime happened from the text
def getTime(text):
	temp = re.search(r'(\d+:\d+) ([aApP]\.[mM]\.)',text)#9:19 p.m.
	#Since the time format in the text may be different, will need to consider every possible format.
	if temp:
		if temp.group(2) == "p.m." or temp.group(2) == "P.M.":
			if re.search(r'^12',temp.group(1)):
				return(temp.group(1))
			else:
				temp_li = temp.group(1).split(":")
				hour = int(temp_li[0]) + 12
				temp_li[0] = str(hour)
				return(":".join(temp_li))
		elif re.search(r'^12',temp.group(1)) and (temp.group(2) == "a.m." or temp.group(2) == "A.M."):
			temp_li = temp.group(1).split(":")
			temp_li[0] = "00"
			return(":".join(temp_li))
		else:
			return(temp.group(1))
	
#The main function to clean the data
def dataClean(year,htmlLines, file1, file2):
	#Concat the parameter year and "20" so that the year will be in format 20xx
	temp_year = "20"+year
	#Read each line in the html
	for i in htmlLines:
		temp = re.search(r'<td><b>(.*)</b><br/>(.*)</td>',i)
		#Retrieve date
		date = getDate(i)
		if date:
			csvwrite.append(date)
		else:
			csvwrite.append("null")
		#Retrieve url
		case_url = getUrl(i)
		#If there is a match, go to the link and retireve the time
		if case_url:
			case_url = url_detail + case_url
			temp_page = requests.get(case_url)
			time = getTime(temp_page.text)
			if time:
				csvwrite.append(time)
			else:
				csvwrite.append("null")
			#Write the data in csvwrite with delimiter commoma
			file2.writerow(csvwrite)
			#Clean csvwrite
			del csvwrite[:]
		#If find a match, retrieve the location and send the location to GoogleMap API to get the longitude and lattitude
		if temp:
			result = cleanLocation(temp.group(2))
			if result != "":
				# c+=1
				# print(str(c)+": ",result, " " + temp.group(1))
				result_code = getGeoCode(gmaps,result)[0]
				lng = result_code['geometry']['location']['lng']
				lat = result_code['geometry']['location']['lat']
				
				toWrite = "new google.maps.LatLng(" + str(lat) +", "+str(lng)+"),"
				#Save the toWrite in another file, which will be used in the visualization html
				file1.write(toWrite)
				file1.write("\n")
				csvwrite.append(temp_year)
				csvwrite.append(temp.group(1))
				csvwrite.append(result)
				csvwrite.append(str(lat))
				csvwrite.append(str(lng))

#The column names of the csv file
CSV_COLUMN_NAME = ['Date','Year','Crime','Address','Lat','Lng','Time']

#Open the csv file to write
with open("umd_crime.csv","w") as f2:
	writer = csv.writer(f2)
	writer.writerow(CSV_COLUMN_NAME)
	#Open the text file to write
	with open("umd_crime2.txt","w") as f:
		for i in YEAR:
			temp_url = url + i
			#Go to links of crimes happened each year and retireve the text
			page = requests.get(temp_url)
			#Pass the text and retireve every needed information, including date, year, crime, location, and time
			dataClean(i,page.text.split('\n'), f, writer)
			

			# writer = csv.writer(f)
		 #    writer.writerow(CSV_COLUMN_NAME)
		 #    toCsv(inputdata,writer)
# geocode_result = gmaps.geocode('8150 Baltimore Ave, College Park, MD 20740')
# test = geocode_result[0]
# print("lat:", test['geometry']['location']['lat'],", lng:",test['geometry']['location']['lng'])
# print(test['geometry']['location']['lat'])




