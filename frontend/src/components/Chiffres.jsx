function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("fr-FR", { day: "2-digit", month: "long", hour: "2-digit", minute: "2-digit" });
}

export default function Chiffres({ stats, onActualiser, actualisation }) {
  const p = stats?.dernier_passage;
  return (
    <section id="chiffres" className="chiffres">
      <div className="chiffre">
        <strong>{stats?.offres_actives ?? "—"}</strong>
        <span>offres en ligne</span>
      </div>
      <div className="chiffre">
        <strong>{stats?.par_source?.length ?? "—"}</strong>
        <span>sources réunies</span>
      </div>
      <div className="chiffre">
        <strong>{stats?.abonnes ?? "—"}</strong>
        <span>abonnés</span>
      </div>
      <div className="chiffre">
        <strong className="petit">{formatDate(p?.date)}</strong>
        <span>
          dernière vérification
          {p?.date && ` · ${p.nouvelles} nouvelle${p.nouvelles > 1 ? "s" : ""}`}
        </span>
        <button className="lien" onClick={onActualiser} disabled={actualisation}>
          {actualisation ? "Vérification…" : "Vérifier maintenant"}
        </button>
      </div>
    </section>
  );
}
