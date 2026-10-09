// Section "Tendances" : les resultats du WEB USAGE MINING, montres aux visiteurs.
export default function Tendances({ usage, onOuvrir }) {
  if (!usage) return null;
  const offres = usage.offres_populaires || [];
  const categories = usage.categories_populaires || [];
  const associations = usage.associations || [];
  if (offres.length === 0 && categories.length === 0) return null;   // pas encore de donnees

  const max = Math.max(...categories.map((c) => c.vues), 1);

  return (
    <section id="tendances" className="section tendances">
      <div className="section-titre">
        <span className="surtitre">Web usage mining</span>
        <h2>Les tendances</h2>
        <p className="tendances-intro">
          Ce que regardent les {usage.sessions} visiteurs du site : calculé à partir de leurs clics, de façon anonyme.
        </p>
      </div>

      <div className="tendances-grille">
        <div>
          <h3 className="tendances-titre">Les offres les plus consultées</h3>
          <ol className="classement">
            {offres.map((o, i) => (
              <li key={o.id} onClick={() => onOuvrir(o.id)}>
                <span className="rang">{String(i + 1).padStart(2, "0")}</span>
                <span className="classement-texte">
                  <strong>{o.titre}</strong>
                  <small>{o.entreprise} · {o.vues} vue{o.vues > 1 ? "s" : ""}</small>
                </span>
              </li>
            ))}
          </ol>
        </div>

        <div>
          <h3 className="tendances-titre">Les catégories les plus regardées</h3>
          <ul className="barres">
            {categories.map((c) => (
              <li key={c.categorie}>
                <span className="barre-label">{c.categorie}</span>
                <span className="barre-fond">
                  <span className="barre" style={{ width: `${(100 * c.vues) / max}%` }} />
                </span>
                <span className="barre-valeur">{c.vues}</span>
              </li>
            ))}
          </ul>

          {associations.length > 0 && (
            <>
              <h3 className="tendances-titre espace">Ceux qui regardent… regardent aussi</h3>
              <ul className="associations">
                {associations.slice(0, 3).map((a) => (
                  <li key={a.a + a.b}>
                    <em>{a.confiance} %</em> des visiteurs intéressés par <strong>{a.a}</strong> consultent
                    aussi <strong>{a.b}</strong>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
