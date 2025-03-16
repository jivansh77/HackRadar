"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useSearchParams } from "next/navigation";
import { FilterState } from "./HackathonFilters";

// Define the Hackathon type
interface Hackathon {
  id: number;
  name: string;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  location: string | null;
  registration_link: string;
  source: string;
  image_url: string | null;
}

interface HackathonListProps {
  filters?: FilterState;
}

export default function HackathonList({ filters }: HackathonListProps) {
  const [hackathons, setHackathons] = useState<Hackathon[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  const searchParams = useSearchParams();
  
  // Fetch hackathons from the API
  useEffect(() => {
    const fetchHackathons = async () => {
      try {
        // In a real app, this would be an environment variable
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
        
        const response = await fetch(`${apiUrl}/hackathons`);
        
        if (!response.ok) {
          throw new Error(`Error fetching hackathons: ${response.statusText}`);
        }
        
        const data = await response.json();
        setHackathons(data);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching hackathons:", err);
        setError("Failed to load hackathons. Please try again later.");
        setLoading(false);
        
        // Show error toast
        toast.error("Failed to load hackathons", {
          description: "Please try again later",
        });
      }
    };
    
    fetchHackathons();
  }, []);
  
  // Apply filters to hackathons
  const filteredHackathons = useMemo(() => {
    // Get filters from props or URL params
    const searchTerm = filters?.searchTerm || searchParams?.get("search") || "";
    const location = filters?.location || searchParams?.get("location") || "all-locations";
    const source = filters?.source || searchParams?.get("source") || "all-platforms";
    const dateRange = filters?.dateRange || searchParams?.get("dateRange") || "any-time";
    
    // Debug output for Unstop hackathons - only log when we actually have data
    if (hackathons.length > 0) {
      const unstopHackathons = hackathons.filter(h => h.source === "Unstop");
      
      // Only log if we have Unstop hackathons or this is the first time we're seeing data
      if (unstopHackathons.length > 0) {
        console.log(`Total Unstop hackathons: ${unstopHackathons.length}`);
        console.log(`Unstop hackathons with dates in the future: ${
          unstopHackathons.filter(h => h.start_date && new Date(h.start_date) > new Date()).length
        }`);
        console.log(`Unstop hackathons with dates in the past: ${
          unstopHackathons.filter(h => h.start_date && new Date(h.start_date) <= new Date()).length
        }`);
        console.log(`Current filter settings - Source: ${source}, DateRange: ${dateRange}, Location: ${location}`);
      }
    }
    
    return hackathons.filter(hackathon => {
      // Filter by search term
      if (searchTerm && !hackathon.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
          !(hackathon.description && hackathon.description.toLowerCase().includes(searchTerm.toLowerCase()))) {
        return false;
      }
      
      // Filter by location
      if (location !== "all-locations" && hackathon.location !== location) {
        // Special handling for "Online | City" format
        if (location === "Online" && hackathon.location?.startsWith("Online |")) {
          // Allow "Online" filter to show "Online | City" events
          return true;
        } else if (location !== "Online" && hackathon.location?.includes(location)) {
          // For city filters like "Mumbai", show both "Mumbai" and "Online | Mumbai"
          return true;
        }
        return false;
      }
      
      // Filter by source
      if (source !== "all-platforms" && hackathon.source !== source) {
        return false;
      }
      
      // Filter by date range - with improved logic
      if (dateRange !== "any-time" && hackathon.start_date) {
        const today = new Date();
        const startDate = new Date(hackathon.start_date);
        
        // Upcoming: future events
        if (dateRange === "upcoming" && startDate <= today) {
          return false;
        }
        
        // Past events: only show events that have already happened
        if (dateRange === "past-events" && startDate > today) {
          return false;
        }
        
        // This week
        if (dateRange === "this-week") {
          const endOfWeek = new Date();
          endOfWeek.setDate(today.getDate() + (7 - today.getDay()));
          
          if (startDate < today || startDate > endOfWeek) {
            return false;
          }
        }
        
        // This month
        if (dateRange === "this-month") {
          const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);
          
          if (startDate < today || startDate > endOfMonth) {
            return false;
          }
        }
        
        // Next month
        if (dateRange === "next-month") {
          const startOfNextMonth = new Date(today.getFullYear(), today.getMonth() + 1, 1);
          const endOfNextMonth = new Date(today.getFullYear(), today.getMonth() + 2, 0);
          
          if (startDate < startOfNextMonth || startDate > endOfNextMonth) {
            return false;
          }
        }
      }
      
      return true;
    });
  }, [hackathons, filters, searchParams]);
  
  // Format date for display
  const formatDate = (dateString: string | null) => {
    if (!dateString) return "TBA";
    
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };
  
  // Get source badge color
  const getSourceColor = (source: string) => {
    switch (source.toLowerCase()) {
      case "unstop":
        return "bg-blue-100 text-blue-800";
      case "devfolio":
        return "bg-green-100 text-green-800";
      case "devpost":
        return "bg-purple-100 text-purple-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="text-center p-8 bg-red-50 rounded-lg">
        <h3 className="text-xl font-semibold text-red-800 mb-2">Error</h3>
        <p className="text-red-600">{error}</p>
        <Button 
          className="mt-4" 
          variant="outline"
          onClick={() => window.location.reload()}
        >
          Try Again
        </Button>
      </div>
    );
  }
  
  if (filteredHackathons.length === 0) {
    return (
      <div className="text-center p-8 bg-gray-50 rounded-lg">
        <h3 className="text-xl font-semibold text-gray-800 mb-2">No Hackathons Found</h3>
        <p className="text-gray-600">Try adjusting your filters or check back later for upcoming hackathons.</p>
      </div>
    );
  }
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      {filteredHackathons.map((hackathon) => (
        <Card key={hackathon.id} className="overflow-hidden hover:shadow-lg transition-shadow">
          {/* Image display removed */}
          
          <CardHeader>
            <div className="flex justify-between items-start">
              <CardTitle className="text-xl">{hackathon.name}</CardTitle>
              <Badge className={getSourceColor(hackathon.source)}>
                {hackathon.source}
              </Badge>
            </div>
            {hackathon.location && (
              <CardDescription>
                <span className="flex items-center gap-1">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {hackathon.location}
                </span>
              </CardDescription>
            )}
          </CardHeader>
          
          <CardContent>
            {hackathon.description && (
              <p className="text-gray-600 mb-4 line-clamp-3">{hackathon.description}</p>
            )}
            
            <div className="flex flex-col gap-1 text-sm">
              {hackathon.start_date && (
                <div className="flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span>
                    {formatDate(hackathon.start_date)} 
                    {hackathon.end_date && ` - ${formatDate(hackathon.end_date)}`}
                  </span>
                </div>
              )}
            </div>
          </CardContent>
          
          <CardFooter>
            <Button asChild className="w-full">
              <a href={hackathon.registration_link} target="_blank" rel="noopener noreferrer">
                Register Now
              </a>
            </Button>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
} 