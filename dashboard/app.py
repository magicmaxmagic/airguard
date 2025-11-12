import streamlit as st, requests, pandas as pd, time

API_URL = "http://127.0.0.1:8000/events/"
st.set_page_config(page_title="AirGuard Dashboard", layout="wide")
st.title("🏠 AirGuard – Tableau de bord local")

refresh = st.sidebar.slider("Rafraîchissement (s)", 1, 10, 3)
limit = st.sidebar.slider("Limite affichage", 10, 200, 100)
placeholder = st.empty()

while True:
    try:
        res = requests.get(API_URL)
        if res.status_code == 200:
            data = res.json()
            df = pd.DataFrame(data)
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp", ascending=False).head(limit)
                with placeholder.container():
                    st.metric("Total alertes", len(df))
                    st.line_chart(df, x="timestamp", y="value", height=300)
                    st.dataframe(df)
            else:
                st.info("Aucune alerte reçue.")
        else:
            st.error(f"Erreur API {res.status_code}")
    except Exception as e:
        st.warning(f"Connexion impossible : {e}")
    time.sleep(refresh)