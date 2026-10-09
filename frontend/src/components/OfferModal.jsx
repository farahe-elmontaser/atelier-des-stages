import { useEffect } from "react";

export default function OfferModal({ offre, onFermer, onClicOrigine }) {
  // Fermer avec la touche Echap
  useEffect(() => {
    const f = (e) => e.key === "Escape" && onFermer();
    window.addEventListener("keydown", f);
    return () => window.removeEventListener("keydown", f);
  }, [onFermer]);

  return (
    <div className="modal-fond" onClick={onFermer}>
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <button className="modal-fermer" onClick={onFermer} aria-label="Fermer">×</button>
        <span className="carte-categorie">{offre.categorie}</span>
        <h2>{offre.titre}</h2>
        <p className="carte-entreprise">
          {offre.entreprise}
          <span className="point">·</span>
          {offre.ville}
        </p>

        {offre.competences?.length > 0 && (
          <div className="competences">
            {offre.competences.map((c) => <span key={c}>{c}</span>)}
          </div>
        )}

        <p className="modal-description">{offre.description || "Pas de description."}</p>

        <dl className="modal-infos">
          <div><dt>Source</dt><dd>{offre.source}</dd></div>
          {offre.date_publication && <div><dt>Publiée le</dt><dd>{offre.date_publication.slice(0, 10)}</dd></div>}
        </dl>

        {/^https?:\/\//.test(offre.lien || "") ? (
          <a href={offre.lien} target="_blank" rel="noreferrer" className="bouton" onClick={onClicOrigine}>
            Voir l'offre d'origine
          </a>
        ) : (
          <p className="note-demo">
            Offre fictive du mode démo : elle n'a pas de page d'origine.
            Les offres des vraies sources (scraping, Adzuna, France Travail, Job Bank) ont un lien.
          </p>
        )}
      </div>
    </div>
  );
}
