import json
import pandas as pd
from glob import glob
import matplotlib.pyplot as plt

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from enum import Enum

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

docs = db.collection(u'scoutresults').stream()
data = []

for doc in docs:
    dict = doc.to_dict()
    data.append(dict)

# read json files

# files = glob("data/*json")
# data = {}
# for file in files:
#     data[file] = json.load(open(file))

# set up dataframe

# df = pd.DataFrame(data).T
# df = df.reset_index()
# df = df.drop('index',axis=1)
df = pd.DataFrame(data)
df = df.apply(pd.to_numeric, errors='ignore')
df = df.astype(int, errors='ignore')
df = df.set_index(['team_number', 'match_number'])
df = df.sort_index(level=[0,1], ascending = True)

columns = df.columns.tolist()
special = ['can_move', 'can_hang', 'student_name', 'comments']
columns = [c for c in columns if c not in special] + special
df = df[columns]

# write file for import to tableau -- we probably don't need this

#df.to_csv('tableau.csv')

# set up team summaries

teams = df.groupby(level=0).mean()
teams = teams.reset_index()
team_dict = {str(t): str(t)+'.html' for t in teams['team_number']}

# prepare to print to html

header = '''<html>
<head>
<link rel='stylesheet' type='text/css' href="css/jquery.dataTables.min.css" />
<link rel='stylesheet' type='text/css' href="css/buttons.dataTables.min.css" />
<script type="text/javascript" src="js/jquery.js"> </script>
<script type="text/javascript" src="js/jquery.dataTables.min.js"> </script>
<script type="text/javascript" src="js/dt.js"> </script>
</head>
<body>
'''
footer = '''
</body>
</html>
'''

def mkpage(html_string, filename):
    html_string = html_string.replace(r'<td>',r'<td align=center>')
    output = open(r'web/'+filename, 'w')
    output.write(header + html_string + footer)
    output.close()

# Write out the main summary html page
#
#   add links to individual team pages

html_string = teams.to_html(table_id='example',
                               index=False,
                               float_format=r'%0.2f',
                               classes='display',
                               border=0)

for k, v in team_dict.items():
    html_string = html_string.replace(k, r'<a href="' + v +'">' + k + r'</a>')

mkpage(html_string, 'teams.html')

# Write out the individual team pages

for team, frame in df.groupby(level=0):
    html_string = frame.to_html(table_id='example',
                                index=False,
                                float_format=r'%0.2f',
                                classes='display',
                                justify='center',
                                border=0)
    mkpage(html_string, str(team)+'.html')
