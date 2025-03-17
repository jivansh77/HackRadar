"use client";

import { useState, useCallback, Suspense } from "react";
import HackathonList from "@/components/HackathonList";
import HackathonFilters, { FilterState } from "@/components/HackathonFilters";
import { Toaster } from "@/components/ui/sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Fallback UI for HackathonFilters when it's suspended
function FiltersLoading() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <div className="h-6 w-40 bg-gray-200 rounded animate-pulse"></div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {Array(4).fill(0).map((_, i) => (
          <div key={i} className="space-y-2">
            <div className="h-4 w-24 bg-gray-200 rounded animate-pulse"></div>
            <div className="h-10 w-full bg-gray-200 rounded animate-pulse"></div>
          </div>
        ))}
        <div className="pt-2 space-y-2">
          <div className="h-10 w-full bg-gray-200 rounded animate-pulse"></div>
          <div className="h-10 w-full bg-gray-200 rounded animate-pulse"></div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function Home() {
  const [filters, setFilters] = useState<FilterState>({
    searchTerm: "",
    location: "all-locations",
    source: "all-platforms",
    dateRange: "any-time"
  });

  const handleFilterChange = useCallback((newFilters: FilterState) => {
    setFilters(newFilters);
  }, []);

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8 px-4">
        <header className="mb-8 text-center">
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Discover upcoming hackathons from Unstop, Devfolio, and Devpost all in one place.
            Get real-time updates and never miss an opportunity!
          </p>
        </header>
        
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <Suspense fallback={<FiltersLoading />}>
              <HackathonFilters onFilterChange={handleFilterChange} />
            </Suspense>
          </div>
          <div className="lg:col-span-3">
            <Suspense fallback={<div className="h-96 bg-gray-200 rounded animate-pulse"></div>}>
              <HackathonList filters={filters} />
            </Suspense>
          </div>
        </div>
      </div>
      <Toaster />
    </main>
  );
}
