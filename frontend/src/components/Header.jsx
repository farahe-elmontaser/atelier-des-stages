import Emblem from "./Emblem";

export default function Header() {
  return (
    <header className="header">
      <div className="bandeau">Nouvelles offres vérifiées automatiquement, chaque heure</div>
      <div className="header-centre">
        <a href="#" className="logo">
          <Emblem />
          <span className="logo-nom">L'Atelier des Stages</span>
          <span className="logo-sous">Paris · Casablanca · Montréal</span>
        </a>
      </div>
      <nav className="nav">
        <a href="#offres">Les offres</a>
        <a href="#chiffres">La maison</a>
        <a href="#abonnement">S'abonner</a>
      </nav>
    </header>
  );
}
