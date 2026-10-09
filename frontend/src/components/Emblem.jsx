// Embleme original de la marque (une plume dans un cercle)
export default function Emblem({ size = 44 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <circle cx="24" cy="24" r="22.5" stroke="currentColor" strokeWidth="1" />
      <circle cx="24" cy="24" r="19" stroke="currentColor" strokeWidth="0.5" />
      <path d="M31 13c-7 2-12 8-13 17l-2 5" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" />
      <path d="M31 13c-1 6-5 11-12 14" stroke="currentColor" strokeWidth="0.8" strokeLinecap="round" />
      <path d="M14 36h12" stroke="currentColor" strokeWidth="0.8" strokeLinecap="round" />
    </svg>
  );
}
