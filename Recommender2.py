from osuapi import OsuApi, ReqConnector
import requests
import json
import sqlite3
import datetime

with open("apicode.json") as apc:
	apicode = json.load(apc)[0]["apicode"]

api = OsuApi(apicode, connector = ReqConnector())
playername = "potla"
user = api.get_user(playername) 

def compare_maps(a, b):
	affinity = 0
	ID1 = a.split(" ")[0]
	ID2 = b.split(" ")[0]
	if ID1 != ID2:
		return 0
	if "NoMod" in a and "NoMod" in b:
		return 2
	if "Hidden" in a and "Hidden" in b:
		affinity += 1
	if "HardRock" in a and "HardRock" in b:
		affinity += 1
	if "DoubleTime" in a or "Nightcore" in a and "DoubleTime" in b or "Nightcore" in b:
		affinity += 1
	return affinity

def mod_finder(score, counter):
	ID = score.split(" ")[0]
	if "NoMod" in score:
		counter[ID]["NoMod"] += 1
	if "HardRock" in score:
		counter[ID]["HardRock"] += 1
	if "DoubleTime" in score or "Nightcore" in score:
		counter[ID]["DoubleTime"] += 1

def findmaxmod(ID, counter):
	v = list(counter[ID].values())
	k = list(counter[ID].keys())
	return k[v.index(max(v))]


conn = sqlite3.connect('osu.db')
c = conn.cursor()

with open("updated_player_records.json") as fr:
	playerdb = json.load(fr)


user_rank = user[0].pp_rank
similar_users = []
for player in playerdb:
	player_rank = int(player["global_rank"])
	if (player_rank - user_rank <= 800 and player_rank - user_rank >= 0) or (user_rank - player_rank >= 200 and user_rank - player_rank >= 0):
		similar_users.append(player["user_id"])
	if len(similar_users) >= 950:
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
		try:
			c.execute("INSERT INTO PLAYERS VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(scores))
		except:
			pass
	conn.commit()

results = api.get_user_best(playername, limit=25)
userscores = []
scoreidonly = []
for x in results:
	score = str(x.beatmap_id) + " " + str(x.enabled_mods)
	userscores.append(score)
	scoreidonly.append(str(x.beatmap_id))	

bestfriends = []
affinities = {}
for similar_user in similar_users:
	cp = c.execute("SELECT * FROM PLAYERS WHERE PLAYER_ID=?",(similar_user,))
	playerscores = cp.fetchone()
	total_affinity = 0
	if playerscores is None:
		continue
	for i in range(1,26):
		for j in range(25):
			affinity = compare_maps(playerscores[i],userscores[j])
			total_affinity += affinity
	affinities[similar_user] = total_affinity
for key in sorted(affinities, key=affinities.__getitem__, reverse = True):
	bestfriends.append(key)
bestfriends = bestfriends[:10]

#gets most uncommon maps
mapcounts = {}
modcounter = {}
for bestfriend in bestfriends:
	cp = c.execute("SELECT * FROM PLAYERS WHERE PLAYER_ID=?",(bestfriend,))
	playerscores = cp.fetchone()
	for i in range(1,26):
		if playerscores[i].split(" ")[0] in mapcounts:
			mapcounts[playerscores[i].split(" ")[0]] += 1
		else:
			mapcounts[playerscores[i].split(" ")[0]] = 1
			modcounter[playerscores[i].split(" ")[0]] = {"NoMod" : 0, "HardRock" : 0, "DoubleTime" : 0}
		mod_finder(playerscores[i], modcounter) 		 
dump = []
for x in sorted(mapcounts, key=mapcounts.__getitem__):
	dump.append(x)


#get map details
filename=playername+"_"+str(datetime.date.today())
fw=open("Users\\"+filename+".txt","w")
for i in range(100):
	c.execute("CREATE TABLE IF NOT EXISTS BEATMAPS(BEATMAP_ID INTEGER, TITLE TEXT, LINK TEXT, CREATOR TEXT, BPM REAL, SR REAL, LENGTH INTEGER, DIFFICULTY TEXT)")
	try:
		map = dump[i].split(" ")
		if map[0] in scoreidonly:
			continue
	except:
		pass
	c.execute("SELECT * FROM BEATMAPS WHERE BEATMAP_ID=?", (int(map[0]),))
	data = c.fetchone()
	if data is None:
		result = api.get_beatmaps(beatmap_id=int(map[0]))
		if len(result) == 0:
			continue
		link = ("https://osu.ppy.sh/b/"+str(map[0]) + "?m=0")
		c.execute("INSERT INTO BEATMAPS VALUES(?,?,?,?,?,?,?,?)", (int(map[0]), result[0].title, link,result[0].creator, result[0].bpm, result[0].difficultyrating, result[0].total_length, result[0].version))		
	c.execute("SELECT * FROM BEATMAPS WHERE BEATMAP_ID=?", (int(map[0]),))
	data = c.fetchone()
	mod = findmaxmod(map[0], modcounter)
	outstring=data[1] + "\t" + data[7] + "\t" + mod + "\t" + "SR: " + str(data[5])[:3] + " BPM: " + str(data[4]) + " Length: " + str(data[6])+ " "
	outstring += data[3] + "\t" + data[2]
	fw.write(outstring)
	fw.write("\n")

#final steps
conn.commit()
fw.close()
input("Recommendations stored in folder called Users\nPress any key")