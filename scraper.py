import requests
from bs4 import BeautifulSoup
import json
import os
import pandas as pd
import time

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def get_details(player):
	user_id = player.find(class_ = "ranking-page-table__user-link-text js-usercard").get('data-user-id')
	rank = ("".join((player.find(class_ = "ranking-page-table__column ranking-page-table__column--rank").get_text()).split())).replace("#", "")
	name = "".join((player.find(class_ = "ranking-page-table__user-link-text js-usercard").get_text()).split())
	more_details = player.find_all(class_ = "ranking-page-table__column ranking-page-table__column--dimmed")
	acc = "".join((more_details[0].get_text()).split())
	playcount = "".join((more_details[1].get_text()).split())
	pp = ("".join((player.find(class_ = "ranking-page-table__column ranking-page-table__column--focused").get_text()).split())).replace(",", "")
	entry = {"user_id" : user_id, "rank" : rank, "name" : name, "accuracy" : acc, "playcount" : playcount, "pp" : pp}
	return entry

def get_country_links():
	country_links = []
	for pg_no in range(1,3):
		country_page = requests.get("https://osu.ppy.sh/rankings/osu/country?page=" + str(pg_no))
		soup = BeautifulSoup(country_page.content, 'html.parser')
		countries = soup.find_all('a', class_ = 'ranking-page-table__user-link')
		for country in countries:
			country_links.append(country.get('href'))
	return country_links

def get_player_records():
	country_links = get_country_links()
	player_details = []

	for country in country_links:
		flag = True
		pgno = 1
		while flag is True:
			try:
				print(f'Currently Scraping:{country.split("=")[1]}')
				page = requests.get(country+"&page="+str(pgno))
				soup = BeautifulSoup(page.content, 'html.parser')
				table = soup.find('tbody')
				players = table.find_all('tr')	
				for player in players:				
					entry = get_details(player)
					if (len(player_details)+1) % 3000 == 0:
						time.sleep(60)
					if int(entry['pp']) < 5000:
						flag = False
						break
					player_details.append(entry)
				print(f'Total number of records created = {len(player_details)}')
			except:
				pass
			pgno += 1
	return(player_details)
	
	

def get_top_10k():
	pre_dump = []
	for pgno in range(1,201):
		page = requests.get("https://osu.ppy.sh/rankings/osu/performance?page="+str(pgno))
		cls()
		print(f"Page {pgno} out of 200")
		try:
			soup = BeautifulSoup(page.content, 'html.parser')
			table = soup.find('tbody')
			players = table.find_all('tr')
			for player in players:
				entry = get_details(player)
				pre_dump.append(entry)
		except: 
			pass
	with open("player_records.json", "w") as write_file:
		json.dump(pre_dump, write_file)


player_details = get_player_records()
with open("player_records.json", "w") as write_file:
	json.dump(player_details, write_file)
df = pd.DataFrame(player_details)
print(df.head(50))
print(df.tail(50))
