export default function PageWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen pt-14" style={{ backgroundColor: '#0a0e1a' }}>
      <div className="max-w-screen-2xl mx-auto px-6 py-6">{children}</div>
    </div>
  )
}
