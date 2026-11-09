import type { Metadata } from "next";

import "./globals.scss";

export const metadata: Metadata = {
  title: "Jeremy Baer | Portfolio",
  description: "Chat with my virtual clone",
  icons: {
    icon: "/assets/avatar.png",
    apple: "/assets/avatar.png",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
