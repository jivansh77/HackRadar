import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import UserProfile from "@/components/UserProfile";
import Image from "next/image";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "HackRadar - Find Hackathons",
  description: "Discover hackathons from Unstop, Devfolio, and Devpost all in one place.",
  icons: {
    icon: "/logo2.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <header className="border-b py-4">
            <div className="container flex justify-between items-center mx-auto px-4">
              <div className="flex items-center gap-2">
                <Image src="/logo2.png" alt="HackRadar" width={40} height={40} />
                <h1 className="text-xl font-bold">HackRadar</h1>
              </div>
              <UserProfile />
            </div>
          </header>
          {children}
          <Toaster />
        </AuthProvider>
      </body>
    </html>
  );
}
