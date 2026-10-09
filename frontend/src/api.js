// Toutes les communications avec le backend (API REST FastAPI).
// Grace au proxy de vite.config.js, "/api" pointe vers http://localhost:8000/api

const BASE = "/api";

async function requete(chemin, options = {}) {
  const r = await fetch(BASE + chemin, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    // FastAPI renvoie soit un texte, soit une liste d'erreurs de validation (422)
    const msg = typeof data.detail === "string" ? data.detail : "Données invalides.";
    throw new Error(msg);
  }
  return data;
}

// Identifiant ANONYME de la visite (web usage mining) : aleatoire, garde le temps de l'onglet.
function sessionId() {
  try {
    let id = sessionStorage.getItem("session");
    if (!id) {
      id = Math.random().toString(36).slice(2) + Date.now().toString(36);
      sessionStorage.setItem("session", id);
    }
    return id;
  } catch {
    return "anonyme";
  }
}

export const api = {
  profils: () => requete("/profils"),
  offres: ({ profil, q } = {}) => {
    const p = new URLSearchParams();
    if (profil) p.set("profil", profil);
    if (q) p.set("q", q);
    return requete("/offres?" + p.toString());
  },
  stats: () => requete("/stats"),
  inscription: (data) => requete("/inscription", { method: "POST", body: JSON.stringify(data) }),
  actualiser: () => requete("/refresh", { method: "POST" }),
  usage: () => requete("/usage"),

  // Web usage mining : on enregistre une action du visiteur (sans bloquer le site si ca echoue)
  suivre: (type, infos = {}) => {
    fetch(BASE + "/evenements", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, session: sessionId(), ...infos }),
      keepalive: true,
    }).catch(() => {});
  },
};
