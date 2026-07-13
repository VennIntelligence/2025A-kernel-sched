import type { Copy, LinkKind } from '../lib/i18n'

export function Closing({ copy }: { copy: Copy }) {
  return (
    <section className="prose-section prose-article conclusion-section" aria-labelledby="conclusion-h">
      <h2 id="conclusion-h" className="section-title">{copy.conclusion.title}</h2>
      <p className="conclusion-body">{copy.conclusion.body}</p>
    </section>
  )
}

export function SiteFooter({ copy }: { copy: Copy }) {
  const m = copy.meta
  return (
    <footer className="site-footer">
      <p className="footer-tagline">{m.title}</p>
      <nav className="footer-links" aria-label="Resources">
        {m.links.map((link: { label: string; kind: LinkKind; href: string }) => (
          <a key={link.label} href={link.href} target="_blank" rel="noreferrer">
            {link.label}
          </a>
        ))}
      </nav>
      <p className="footer-note">{copy.footer.note}</p>
    </footer>
  )
}
