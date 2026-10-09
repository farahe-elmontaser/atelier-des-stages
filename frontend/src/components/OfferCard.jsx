export default function OfferCard({ offre, onOuvrir }) {
  return (
    <article className="carte" onClick={onOuvrir} tabIndex={0} onKeyDown={(e) => e.key === "Enter" && onOuvrir()}>
      <span className="carte-categorie">{offre.categorie}</span>
      <h3>{offre.titre}</h3>
      <p className="carte-entreprise">
        {offre.entreprise}
        <span className="point">·</span>
        {offre.ville}
      </p>
      {offre.resume && <p className="carte-resume">{offre.resume}</p>}
      <div className="carte-pied">
        <span className="carte-source">{offre.source}</span>
        <span className="carte-lien">{offre.source?.startsWith("Démo") ? "Démo" : "Découvrir"}</span>
      </div>
    </article>
  );
}
