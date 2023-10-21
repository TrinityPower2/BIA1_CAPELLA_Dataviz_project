import bs4
import plotly.express as px
import plotly.graph_objects as go
import requests
import pandas as pd
import streamlit as st
import datetime
from bs4 import BeautifulSoup

# get the latest data from data gouv
url = 'https://www.data.gouv.fr/api/1/datasets/60ed57a9f0c7c3a1eb29733f'
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    resources_url = data["resources"][0]["latest"]
    df = pd.read_csv(resources_url)
else:
    print(f"Request failed with status code {response.status_code}")

# first block (title)
st.title("Etude des groupes politiques de l'Assemblée nationale")

# second block (qu + date)
col1, col2 = st.columns(2)
with col1:
    st.subheader("Quels groupes sont les plus actifs à l'Assemblée ?")
with col2:
    st.subheader("Date d'actualisation : " + df.loc[0]["dateMaj"],
                 help="Les données sont mises à jour quotidiennement.")

# third block (pie chart)
# pie chart of score_participation
df.sort_values(by="scoreParticipation", ascending=False, inplace=True)
fig = px.pie(df, names='libelle', labels='libelle', values='scoreParticipation',
             title="Répartition du score de participation entre les différents groupes",
             hole=0.4,
             width=800)
fig.update_traces(textposition='outside', textinfo='label', showlegend=False, automargin=True)
st.plotly_chart(fig)


# fourth block (key info of a given group)
@st.cache
display_part = st.selectbox("Choisissez un groupe pour obtenir ses informations", df["libelle"])
display_df = df[df.libelle == display_part].copy()
col1, col2 = st.columns(2)
with col1:
    display_df["women"] = display_df["women"] / 100.0
    display_df["men"] = display_df["women"].map(lambda x: 1 - x)
    st.write("Pourcentage de femmes et d'hommes au sein du groupe")
    @st.cache
    st.bar_chart(display_df, x=None, y=["women", "men"])
with col2:
    display_rank = int(df["scoreParticipation"].rank(ascending=False).loc[display_df.index].iloc[0])
    if display_rank == 1:
        st.metric("Classement en termes de participation", str(display_rank) + 'er')
    else:
        st.metric("Classement en termes de participation", str(display_rank) + 'ème')

    st.metric("Cohésion au sein du groupe", str(round(float(display_df.iloc[0]["socreCohesion"])*100, 1)) + '%')

    st.metric("Score rose",
              str(round(float(display_df.iloc[0]['scoreRose'])*100, 1)) + '%',
              help="Le score rose désigne la représentativité sociale au sein du groupe")

    st.metric("Score majorité",
              str(round(float(display_df.iloc[0]['scoreMajorite'])*100, 1)) + '%',
              help="Le score majorité désigne la proximité du groupe avec la majorité présidentielle")


# Fifth block (most participating group)

# determine the most participating group
highest_part = max(df["scoreParticipation"])
parti_actif = df[df.scoreParticipation == highest_part]["libelle"]
# transform parti actif into string
parti_actif = parti_actif.loc[parti_actif.index[0]]

# display
st.header("Focus sur le groupe le plus actif : " + parti_actif)
st.subheader("Quelques informations clé")
col1, col2, col3 = st.columns(3)
with col1:
    crea_date = df[df.libelle == parti_actif]['dateDebut']
    legis = df[df.libelle == parti_actif]['legislature']
    posPol = df[df.libelle == parti_actif]['positionPolitique']
    age = df[df.libelle == parti_actif]['age']

    crea_date = crea_date.loc[crea_date.index[0]]
    legis = legis.loc[legis.index[0]]
    posPol = posPol.loc[posPol.index[0]]
    age = age.loc[age.index[0]]

    st.metric("Date de création : ", crea_date)
    st.metric("Législature : ", legis)
with col2:
    st.metric("Position politique", posPol)
    st.metric("Age moyen des membres", age)
with col3:
    wom = df[df.libelle == parti_actif]['women'] # women
    cohes = df[df.libelle == parti_actif]['socreCohesion'] # socre cohésion
    majo = df[df.libelle == parti_actif]['scoreMajorite'] # score majorité

    # extract dataframe indicators to obtain float values
    wom = wom.loc[wom.index[0]] / 100.0
    cohes = cohes.loc[cohes.index[0]]
    majo = majo.loc[majo.index[0]]

    st.progress(wom, "Pourcentage de femme au sein du groupe")
    st.progress(cohes, "Degré de cohésion au sein du groupe")
    st.progress(majo, "Proximité par rapport à la majorité")

# focus on Assemblée Nationale topics
st.header("Focus sur l'actualité de l'Assemblée nationale")

st.subheader("Les dernières vidéos youtube de la LCP",
             help="La LCP est le canal de communication officiel de l'Assemblée nationale. "
                  "Ces vidéos ont été récupérées via l'API Youtube de Google")
lcp_id = "UCHGFbA0KWBgf6gMbyUCZeCQ"
my_api_key = "AIzaSyBKNUSPd7-FsuYiLL_425S6GQPYGN0CHTc"
datetime_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)

url = f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&channelId={lcp_id}' \
      f'&videoEmbeddable=True' \
      f'&publishedAfter={datetime_week_ago.isoformat()}Z&maxResults=3&order=date&type=video&key={my_api_key}'
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    video_ids = [i['id']['videoId'] for i in data['items']]
    urls = pd.Series(video_ids)
    urls = urls.map(lambda x: "https://www.youtube.com/watch?v=" + x)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.video(data=urls[0])
    with col2:
        st.video(data=urls[1])
    with col3:
        st.video(data=urls[2])
else:
    print(f"Request failed with status code {response.status_code}")


st.subheader("L'agenda du jour")
agenda_url = "https://www2.assemblee-nationale.fr/agendas/les-agendas"
try:
    response = requests.get(agenda_url, timeout=15)
except:
    st.write("L'accès au site des agendas est actuellement impossible. Merci de réessayer ultérieurement.")
if response.status_code == 200:
    html_code = response.content

    full_page = BeautifulSoup(html_code, "html.parser", from_encoding="UTF-8")
    full_table = full_page.find_all("ul", "liste-agenda-journalier")
    # check if we have events to display
    if len(full_table) == 0:
        st.write("Aucun événement prévu aujourd'hui !")
    else:
        # events' list
        morning_agenda = full_page.find_all("ul", "liste-agenda-journalier journalier matin clearfix")
        afternoon_agenda = full_page.find_all("ul", "liste-agenda-journalier journalier soir clearfix")
        # make sure that we have morning AND afternoon events
        if len(morning_agenda) != 0 and len(afternoon_agenda) != 0:
            morning_agenda = morning_agenda[0]
            afternoon_agenda = afternoon_agenda[0]
            # events time
            morning_hours = morning_agenda.find_all_next("strong")
            afternoon_hours = afternoon_agenda.find_all_next("strong")
            # events name
            morning_events = morning_agenda.find_all_next("span", "titre")
            afternoon_events = afternoon_agenda.find_all_next("span", "titre")
            # remove afternoon events from morning lists
            for hour in afternoon_hours:
                if hour in morning_hours:
                    morning_hours.remove(hour)
            for event in afternoon_events:
                if event in morning_events:
                    morning_events.remove(event)
            # append hour and name + format the html elements
            morning_sum = []
            for i in range(len(morning_hours)):
                morning_sum.append("<li>" + str(morning_hours[i]) + str(morning_events[i]) + "</li>")
            morning_sum = "\n".join(morning_sum)
            afternoon_sum = []
            for i in range(len(afternoon_hours)):
                afternoon_sum.append("<li>" + str(afternoon_hours[i]) + str(afternoon_events[i]) + "</li>")
            afternoon_sum = "\n".join(afternoon_sum)
        # case where we only have afternoon events
        elif len(morning_agenda) == 0 and len(afternoon_agenda) != 0:
            morning_sum = ""
            afternoon_agenda = afternoon_agenda[0]
            # events time
            afternoon_hours = afternoon_agenda.find_all_next("strong")
            # events name
            afternoon_events = afternoon_agenda.find_all_next("span", "titre")
            afternoon_sum = []
            for i in range(len(afternoon_hours)):
                afternoon_sum.append("<li>" + str(afternoon_hours[i]) + str(afternoon_events[i]) + "</li>")
            afternoon_sum = "\n".join(afternoon_sum)
        # case where we only have morning events
        elif len(afternoon_agenda) == 0 and len(morning_agenda) != 0:
            afternoon_sum = ""
            morning_agenda = morning_agenda[0]
            # events time
            morning_hours = morning_agenda.find_all_next("strong")
            # events name
            morning_events = morning_agenda.find_all_next("span", "titre")
            morning_sum = []
            for i in range(len(morning_hours)):
                morning_sum.append("<li>" + str(morning_hours[i]) + str(morning_events[i]) + "</li>")
            morning_sum = "\n".join(morning_sum)
        else:
            st.write("Aucun événement prévu aujourd'hui !")
            morning_sum = ""
            afternoon_sum = ""

        # display
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(morning_sum, unsafe_allow_html=True)
        with col2:
            st.markdown(afternoon_sum, unsafe_allow_html=True)
else:
    print(f"Request failed with status code {response.status_code}")


# Further French politics related inforamation
st.subheader("Quelques articles de presse pour aller plus loin",
             help="Ces articles sont extrait des actualités Google portant sur l'Assemblée nationale. "
                  "Les données ont été récupérées via l'API GNews")
# Get last news using GNews API
gnew_api_key = "bee1e8bfdfd3e0601050ce8c13f7d06c"
gnew_url = f"https://gnews.io/api/v4/top-headlines?category=general&q=assemblee nationale&lang=fr&country=fr&max=3" \
      f"&apikey={gnew_api_key}"
response = requests.get(gnew_url)
if response.status_code == 200:
    data = response.json()
    art_list = []
    for article in data['articles']:
        art_list.append({"titre": article['title'], "url": article['url'], "img": article['image'],
                         "date": article['publishedAt'].split("T")[0], "auteur": article['source']['name']})
    # display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image(art_list[0]["img"])
        st.markdown("<a href=" + art_list[0]['url'] + ">" + art_list[2]["titre"] + "</a>", unsafe_allow_html=True)
        st.write("Publié le " + art_list[0]["date"])
        st.write("Par " + art_list[0]['auteur'])
    with col2:
        st.image(art_list[1]["img"])
        st.markdown("<a href=" + art_list[1]['url'] + ">" + art_list[2]["titre"] + "</a>", unsafe_allow_html=True)

        st.write("Publié le " + art_list[1]["date"])
        st.write("Par " + art_list[1]['auteur'])
    with col3:
        st.image(art_list[2]["img"])
        st.markdown("<a href=" + art_list[2]['url'] + ">" + art_list[2]["titre"] + "</a>", unsafe_allow_html=True)
        st.write("Publié le " + art_list[2]["date"])
        st.write("Par " + art_list[2]['auteur'])
else:
    print(f"Request failed with status code {response.status_code}")


# Sources
st.header("Bibliographie")
col1, col2, col3 = st.columns(3)

with col1:
    st.write("Auteur du site: CAPELLA Jean-Baptiste BIA1 Promo 2025")
    st.link_button("LinkedIn", "https://www.linkedin.com/in/jean-baptiste-capella-ingenieur-data/")
    st.link_button("Github", "https://github.com/TrinityPower2")
with col2:
    st.write("Jeu de données")
    st.link_button("Jeu de données Data gouv",
                   "https://www.data.gouv.fr/fr/datasets/groupes-politiques-actifs-de-lassemblee-nationale-informations-et-"
                   "statistiques/")
with col3:
    st.write("Webscrapping & API")
    st.link_button("Chaine youtube LCP", "https://www.youtube.com/@LCPAssembleenationale/featured")
    st.link_button("Agenda de l'Assemblée", "https://www2.assemblee-nationale.fr/agendas/les-agendas")
    st.link_button("API youtube", "https://developers.google.com/youtube/v3/docs?hl=fr")
    st.link_button("API GNews", "https://gnews.io/docs/v4?python#introduction")
st.subheader("#datavz2023efrei")
