export default function PageHeader({ title, subtitle }) {
  return (
    <div style={{ marginBottom: 24, paddingBottom: 16,
                  borderBottom: '1px solid #1E2D4D' }}>
      <h1 style={{ color: '#E2E8F0', fontSize: '1.6rem',
                   fontWeight: 700, letterSpacing: 2, margin: 0 }}>
        {title}
      </h1>
      {subtitle && (
        <p style={{ color: '#4A5568', fontSize: '0.8rem',
                    marginTop: 4, letterSpacing: 1 }}>
          {subtitle}
        </p>
      )}
    </div>
  )
}