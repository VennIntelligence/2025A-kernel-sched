/** A research figure: responsive image + numbered caption, paper-style. */
export function FigureBlock({
  src,
  alt,
  label,
  caption,
  maxWidth,
  className,
}: {
  src: string
  alt: string
  label: string
  caption: string
  /** Optional cap on rendered width (px) for narrow/portrait figures. */
  maxWidth?: number
  /** Extra class on the <figure> (e.g. to scale or center it). */
  className?: string
}) {
  const href = import.meta.env.BASE_URL + src
  return (
    <figure className={className ? `figure-block ${className}` : 'figure-block'}>
      <div className="figure-block-frame" style={maxWidth ? { maxWidth } : undefined}>
        <img src={href} alt={alt} loading="lazy" decoding="async" />
      </div>
      <figcaption>
        <span className="figure-block-label">{label}</span>
        {caption}
      </figcaption>
    </figure>
  )
}
