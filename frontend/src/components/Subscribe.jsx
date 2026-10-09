import { useState } from "react";
import { api } from "../api";

export default function Subscribe({ profils }) {
  const [form, setForm] = useState({ nom: "", email: "", profil: "" });
  const [etat, setEtat] = useState({ type: "", message: "" });
  const [envoi, setEnvoi] = useState(false);

  const changer = (champ) => (e) => setForm({ ...form, [champ]: e.target.value });

  async function envoyer(e) {
    e.preventDefault();
    if (!form.profil) return setEtat({ type: "erreur", message: "Choisissez un profil." });
    setEnvoi(true);
    try {
      const r = await api.inscription(form);
      setEtat({ type: "succes", message: r.message });
      api.suivre("inscription", { profil: form.profil });
      setForm({ nom: "", email: "", profil: "" });
    } catch (err) {
      setEtat({ type: "erreur", message: err.message });
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <section id="abonnement" className="abonnement">
      <div className="abonnement-texte">
        <span className="surtitre clair">Sur mesure</span>
        <h2>Recevez les offres<br /><em>faites pour vous</em></h2>
        <p>
          Choisissez votre profil. Dès qu'une nouvelle offre correspondante est publiée,
          elle vous est adressée par e-mail. Jamais deux fois la même.
        </p>
      </div>

      <form className="formulaire" onSubmit={envoyer}>
        <label>
          Nom
          <input value={form.nom} onChange={changer("nom")} placeholder="Votre prénom" />
        </label>
        <label>
          E-mail
          <input type="email" required value={form.email} onChange={changer("email")} placeholder="vous@exemple.com" />
        </label>
        <label>
          Profil
          <select value={form.profil} onChange={changer("profil")}>
            <option value="">Choisir un profil</option>
            {profils.map((p) => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
        </label>
        {form.profil && (
          <p className="categories-profil">
            {profils.find((p) => p.id === form.profil)?.categories.join(" · ")}
          </p>
        )}
        <button className="bouton clair" disabled={envoi}>
          {envoi ? "Envoi…" : "S'abonner"}
        </button>
        {etat.message && <p className={"message " + etat.type}>{etat.message}</p>}
      </form>
    </section>
  );
}
