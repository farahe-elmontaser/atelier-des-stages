export default function Hero() {
  return (
    <section className="hero">
      <div className="hero-texte">
        <span className="surtitre clair">Collection Automne 2026</span>
        <h1>
          L'art de trouver
          <br />
          <em>son stage</em>
        </h1>
        <p>
          Nous parcourons pour vous plusieurs sources d'offres, nous les classons avec soin
          grâce à l'intelligence artificielle, et nous vous adressons uniquement celles
          qui vous ressemblent.
        </p>
        <a href="#abonnement" className="bouton clair">Recevoir mes offres</a>
      </div>

      {/* Motif decoratif original, facon carre de soie */}
      <div className="hero-motif" aria-hidden="true">
        <svg viewBox="0 0 400 400">
          <rect x="20" y="20" width="360" height="360" fill="none" stroke="#fff" strokeOpacity=".7" />
          <rect x="34" y="34" width="332" height="332" fill="none" stroke="#fff" strokeOpacity=".35" />
          {Array.from({ length: 12 }).map((_, i) => (
            <ellipse
              key={i}
              cx="200" cy="200" rx="150" ry="46"
              fill="none" stroke="#fff" strokeOpacity=".55" strokeWidth=".8"
              transform={`rotate(${i * 15} 200 200)`}
            />
          ))}
          <circle cx="200" cy="200" r="34" fill="none" stroke="#fff" strokeOpacity=".9" />
          <circle cx="200" cy="200" r="6" fill="#fff" fillOpacity=".9" />
          {[[60, 60], [340, 60], [60, 340], [340, 340]].map(([x, y], i) => (
            <g key={i} transform={`translate(${x} ${y})`}>
              <circle r="12" fill="none" stroke="#fff" strokeOpacity=".8" />
              <circle r="3" fill="#fff" fillOpacity=".8" />
            </g>
          ))}
        </svg>
      </div>
    </section>
  );
}
