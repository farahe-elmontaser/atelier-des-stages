// Toutes les communications avec le backend (API REST FastAPI).
// Grace au proxy de vite.config.js, "/api" pointe vers http://localhost:8000/api

const BASE = "/api";

async function requete(chemin, options = {}) {
  const r = await fetch(BASE + chemin, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || "Erreur du serveur");
  return data;
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
  desinscription: (email) => requete("/desinscription/" + encodeURIComponent(email), { method: "DELETE" }),
  actualiser: () => requete("/refresh", { method: "POST" }),
};
