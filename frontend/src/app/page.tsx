import HackathonList from "@/components/HackathonList";
import HackathonFilters from "@/components/HackathonFilters";
import { Toaster } from "@/components/ui/sonner";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8 px-4">
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Hackathon Aggregator</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Discover upcoming hackathons from Unstop, Devfolio, and Devpost all in one place.
            Get real-time updates and never miss an opportunity!
          </p>
        </header>
        
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <HackathonFilters />
          </div>
          <div className="lg:col-span-3">
            <HackathonList />
          </div>
        </div>
      </div>
      <Toaster />
    </main>
  );
}
