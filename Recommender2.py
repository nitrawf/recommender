from osuapi import OsuApi, ReqConnector
import requests
import json
import sqlite3
import datetime

with open("apicode.json") as apc:
	apicode = json.load(apc)[0]["apicode"]

api = OsuApi(apicode, connector = ReqConnector())
playername = "neil123"
user = api.get_user(playername) 

conn = sqlite3.connect('osu.db')
c = conn.cursor()

with open("player_records.json") as fr:
	playerdb = json.load(fr)


user_pp = user[0].pp_raw
similar_users = []
for player in playerdb:
	player_pp = int(player["pp"].replace(",",""))
	if (player_pp - user_pp <= 500 and player_pp - user_pp >= 0) or (user_pp - player_pp >= 200 and user_pp - player_pp >= 0):
		similar_users.append(player["user_id"])
	if len(similar_users) >= 50:
		break


#create table for db
str2 = "PLAYER_ID INTEGER PRIMARY KEY"
for i in range(25):
	str2 += ",PLAY"+str(i)+" TEXT"
c.execute("CREATE TABLE IF NOT EXISTS PLAYERS(%s)"%str2)


#get beatmaps of similar users
counter = 0
for player in similar_users:
	counter += 1
	if counter % 50 == 0:
		print("Creating record for %d"%counter)
		conn.commit()
	c.execute("SELECT * FROM PLAYERS WHERE PLAYER_ID=?",(player,))
	data=c.fetchone()
	if data is None:
		results = api.get_user_best(int(player), limit=25)
		scores = [player]
		for x in results:
			scores.append(str(x.beatmap_id) + " " + str(x.enabled_mods))
		c.execute("INSERT INTO PLAYERS VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(scores))
		#print("something broke")
	conn.commit()

results = api.get_user_best( playername, limit=25)
userscores = []
for x in results:		
	userscores.append(str(x.beatmap_id) + " " + str(x.enabled_mods))		

#crates best frands
playerscore = {}
counts = {}
for x in userscores:
	playerscore[x] = 1
for x in similar_users:
	temp = playerscore.copy()
	cp = c.execute("SELECT * FROM PLAYERS WHERE PLAYER_ID=?",(x,))
	data = cp.fetchone()
	count = 0
	try:
		for y in data:
			if y in temp:
				count += 1
	except:
		print("something broke v2")
	counts[x] = count
bestfrands=[]
for key in sorted(counts,key=counts.__getitem__,reverse=True):
	bestfrands.append(key)
bestfrands = bestfrands[0:25]
print(bestfrands)

#gets most uncommon maps
dict1={}
for x in bestfrands:
	cp = c.execute("SELECT * FROM PLAYERS WHERE PLAYER_ID=?",(x,))
	data = cp.fetchone()
	try:
		for y in data:
			if y in dict1:
				dict1[y] += 1
			else:
				dict1[y] = 1 
	except:
		print("something broke v3")
	dump = []
for x in sorted(dict1, key=dict1.__getitem__):
	dump.append(x)


#get map details
filename=playername+"_"+str(datetime.date.today())
fw=open("Users\\"+filename+".txt","w")
for i in range(25):
	c.execute("CREATE TABLE IF NOT EXISTS BEATMAPS(BEATMAP_ID INTEGER,TITLE TEXT,LINK TEXT,CREATOR TEXT)")
	try:
		map = dump[i].split(" ")
	except:
		pass
	c.execute("SELECT * FROM BEATMAPS WHERE BEATMAP_ID=?", (int(map[0]),))
	data = c.fetchone()
	if data is None:
		result = api.get_beatmaps(beatmap_id=int(map[0]))
		if len(result) == 0:
			continue
		link = ("https://osu.ppy.sh/b/"+str(map[0]) + "?m=0")
		c.execute("INSERT INTO BEATMAPS VALUES(?,?,?,?)", (int(map[0]),result[0].title,link,result[0].creator))		
	c.execute("SELECT * FROM BEATMAPS WHERE BEATMAP_ID=?", (int(map[0]),))
	data = c.fetchone()
	outstring=data[1] + "\t" + map[1] + "\t"
	if len(map) == 3:
		outstring += map[2]+"\t"
	outstring += data[3] + "\t" + data[2]
	fw.write(outstring)
	fw.write("\n")

#final steps
conn.commit()
fw.close()
input("Recommendations stored in folder called Users\nPress any key")