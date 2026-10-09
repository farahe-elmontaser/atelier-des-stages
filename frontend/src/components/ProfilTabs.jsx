export default function ProfilTabs({ profils, actif, onChange }) {
  return (
    <div className="onglets" role="tablist">
      <button className={actif === "" ? "actif" : ""} onClick={() => onChange("")}>
        Toutes
      </button>
      {profils.map((p) => (
        <button key={p.id} className={actif === p.id ? "actif" : ""} onClick={() => onChange(p.id)}>
          {p.label}
        </button>
      ))}
    </div>
  );
}
