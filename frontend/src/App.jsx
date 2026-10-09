import { useEffect, useState } from "react";
import { api } from "./api";
import Header from "./components/Header";
import Hero from "./components/Hero";
import Chiffres from "./components/Chiffres";
import ProfilTabs from "./components/ProfilTabs";
import OfferCard from "./components/OfferCard";
import OfferModal from "./components/OfferModal";
import Subscribe from "./components/Subscribe";
import Tendances from "./components/Tendances";
import Footer from "./components/Footer";

let visiteEnregistree = false;   // evite de compter 2 fois la visite (React StrictMode en developpement)

export default function App() {
  const [profils, setProfils] = useState([]);
  const [profil, setProfil] = useState("");          // "" = toutes les offres
  const [recherche, setRecherche] = useState("");
  const [offres, setOffres] = useState([]);
  const [stats, setStats] = useState(null);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState("");
  const [selection, setSelection] = useState(null);  // offre ouverte dans la fenetre
  const [actualisation, setActualisation] = useState(false);
  const [messageRefresh, setMessageRefresh] = useState("");
  const [usage, setUsage] = useState(null);

  // Au demarrage : profils + statistiques
  useEffect(() => {
    api.profils().then(setProfils).catch(() => {});
    api.stats().then(setStats).catch(() => {});
    api.usage().then(setUsage).catch(() => {});
    if (!visiteEnregistree) {                               // web usage mining
      visiteEnregistree = true;
      api.suivre("visite");
    }
  }, []);

  // Web usage mining : on note le profil choisi et les recherches (apres la frappe)
  useEffect(() => {
    if (profil) api.suivre("filtre_profil", { profil });
  }, [profil]);
  useEffect(() => {
    if (recherche.trim().length < 3) return;
    const t = setTimeout(() => api.suivre("recherche", { recherche: recherche.trim() }), 1200);
    return () => clearTimeout(t);
  }, [recherche]);

  function ouvrirOffre(o) {
    setSelection(o);
    api.suivre("vue_offre", { offre_id: o.id });
  }

  // A chaque changement de profil ou de recherche : on recharge les offres
  useEffect(() => {
    setChargement(true);
    const t = setTimeout(() => {
      api
        .offres({ profil, q: recherche })
        .then((d) => { setOffres(d); setErreur(""); })
        .catch(() => setErreur("Impossible de joindre le serveur. Le backend est-il lancé sur le port 8000 ?"))
        .finally(() => setChargement(false));
    }, 250); // petite attente pendant la frappe
    return () => clearTimeout(t);
  }, [profil, recherche]);

  async function actualiser() {
    setActualisation(true);
    setMessageRefresh("");
    try {
      await api.actualiser();
      const [o, s] = await Promise.all([api.offres({ profil, q: recherche }), api.stats()]);
      setOffres(o);
      setStats(s);
    } catch (e) {
      setMessageRefresh(e.message);   // ex. "patientez 30 secondes"
    } finally {
      setActualisation(false);
    }
  }

  return (
    <>
      <Header />
      <main>
        <Hero />
        <Chiffres stats={stats} onActualiser={actualiser} actualisation={actualisation} message={messageRefresh} />

        <section id="offres" className="section">
          <div className="section-titre">
            <span className="surtitre">La collection</span>
            <h2>Les offres du moment</h2>
          </div>

          <ProfilTabs profils={profils} actif={profil} onChange={setProfil} />

          <div className="recherche">
            <input
              type="search"
              placeholder="Rechercher un intitulé, une entreprise, une ville…"
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
            />
          </div>

          {erreur && <p className="message erreur">{erreur}</p>}

          {!erreur && (
            <p className="compteur">
              {chargement ? "Chargement…" : `${offres.length} offre${offres.length > 1 ? "s" : ""}`}
            </p>
          )}

          <div className="grille">
            {offres.map((o) => (
              <OfferCard key={o.id} offre={o} onOuvrir={() => ouvrirOffre(o)} />
            ))}
          </div>

          {!chargement && !erreur && offres.length === 0 && (
            <p className="message">Aucune offre pour le moment. Revenez bientôt.</p>
          )}
        </section>

        <Tendances usage={usage} onOuvrir={(id) => {
          const o = offres.find((x) => x.id === id);
          if (o) ouvrirOffre(o);
        }} />

        <Subscribe profils={profils} />
      </main>
      <Footer />

      {selection && (
        <OfferModal
          offre={selection}
          onFermer={() => setSelection(null)}
          onClicOrigine={() => api.suivre("clic_origine", { offre_id: selection.id })}
        />
      )}
    </>
  );
}
