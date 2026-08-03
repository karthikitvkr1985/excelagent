export const metadata = {
  title: "Excel Intelligence Agent",
  description: "Upload any Excel sheet — get a refined table, deep insights, and AI-built dashboards.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}