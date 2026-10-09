import Emblem from "./Emblem";

export default function Footer() {
  return (
    <footer className="footer">
      <Emblem size={36} />
      <p className="footer-nom">L'Atelier des Stages</p>
      <p>Sources : pages carrières Greenhouse et Lever · The Muse · Arbeitnow · Remotive · Adzuna · France Travail · Job Bank (Canada)</p>
      <p>Projet de module Web Mining — 2026</p>
    </footer>
  );
}
