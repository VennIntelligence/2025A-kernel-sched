import type { SVGProps } from 'react'

type IconProps = SVGProps<SVGSVGElement> & { size?: number }

function Base({ size = 16, children, ...rest }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      {children}
    </svg>
  )
}

export const PlayIcon = (p: IconProps) => (
  <Base {...p}>
    <path d="M7 4.8v14.4l11.5-7.2z" fill="currentColor" stroke="none" />
  </Base>
)

export const PauseIcon = (p: IconProps) => (
  <Base {...p}>
    <rect x="6" y="4.5" width="4" height="15" rx="1" fill="currentColor" stroke="none" />
    <rect x="14" y="4.5" width="4" height="15" rx="1" fill="currentColor" stroke="none" />
  </Base>
)

export const RestartIcon = (p: IconProps) => (
  <Base {...p}>
    <path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1" />
    <path d="M3.5 2.8v3.4h3.4" />
  </Base>
)

export const StepBackIcon = (p: IconProps) => (
  <Base {...p}>
    <path d="M6 5v14" />
    <path d="M18.5 6.5 10 12l8.5 5.5z" fill="currentColor" stroke="none" />
  </Base>
)

export const StepForwardIcon = (p: IconProps) => (
  <Base {...p}>
    <path d="M18 5v14" />
    <path d="M5.5 6.5 14 12l-8.5 5.5z" fill="currentColor" stroke="none" />
  </Base>
)

export const ArrowRightIcon = (p: IconProps) => (
  <Base {...p}>
    <path d="M4.5 12h15" />
    <path d="m13 5.5 6.5 6.5-6.5 6.5" />
  </Base>
)

export const ChevronDownIcon = (p: IconProps) => (
  <Base {...p}>
    <path d="m5 9 7 7 7-7" />
  </Base>
)

export const CopyIcon = (p: IconProps) => (
  <Base {...p}>
    <rect x="9" y="9" width="11" height="11" rx="2" />
    <path d="M5 15H4.5A1.5 1.5 0 0 1 3 13.5v-9A1.5 1.5 0 0 1 4.5 3h9A1.5 1.5 0 0 1 15 4.5V5" />
  </Base>
)

export const CheckIcon = (p: IconProps) => (
  <Base {...p}>
    <path d="m4.5 12.5 5 5 10-11" />
  </Base>
)

export const PaperIcon = (p: IconProps) => (
  <Base {...p}>
    <path d="M6 2.8h8.2L19 7.6V21.2H6z" />
    <path d="M14 3v5h5" />
    <path d="M9 12.5h7M9 16h7" />
  </Base>
)

export const CodeIcon = (p: IconProps) => (
  <Base {...p}>
    <path d="m8 6.5-6 5.5 6 5.5" />
    <path d="m16 6.5 6 5.5-6 5.5" />
    <path d="m13.5 3.5-3 17" />
  </Base>
)

export const DataIcon = (p: IconProps) => (
  <Base {...p}>
    <ellipse cx="12" cy="5.2" rx="8" ry="2.8" />
    <path d="M4 5.2v13.6c0 1.55 3.58 2.8 8 2.8s8-1.25 8-2.8V5.2" />
    <path d="M4 12c0 1.55 3.58 2.8 8 2.8s8-1.25 8-2.8" />
  </Base>
)

export const ResultsIcon = (p: IconProps) => (
  <Base {...p}>
    <path d="M3.5 20.5h17" />
    <path d="M6.5 20v-7M11.5 20V4.5M16.5 20v-10" />
  </Base>
)

/** Tiny DAG mark used as the site logo. */
export function BrandGlyph({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M6.5 6.8 12 12m0 0 5.5-5.2M12 12v6.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
      <circle cx="5.5" cy="5.5" r="2.6" fill="currentColor" />
      <circle cx="18.5" cy="5.5" r="2.6" fill="currentColor" />
      <circle cx="12" cy="12" r="2.6" fill="currentColor" opacity="0.55" />
      <circle cx="12" cy="20" r="2.6" fill="currentColor" />
    </svg>
  )
}
