import Emblem from "./Emblem";

export default function Footer() {
  return (
    <footer className="footer">
      <Emblem size={36} />
      <p className="footer-nom">L'Atelier des Stages</p>
      <p>Sources : web scraping (requests + BeautifulSoup) · Job Bank (données ouvertes du Canada) · Adzuna · France Travail</p>
      <p>Projet de module Web Mining — 2026</p>
    </footer>
  );
}
