"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useRouter, useSearchParams } from "next/navigation";

interface HackathonFiltersProps {
  onFilterChange?: (filters: FilterState) => void;
}

export interface FilterState {
  searchTerm: string;
  location: string;
  source: string;
  dateRange: string;
}

export default function HackathonFilters({ onFilterChange }: HackathonFiltersProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isInitialMount = useRef(true);
  
  // Initialize state from URL params if available
  const [searchTerm, setSearchTerm] = useState(searchParams?.get("search") || "");
  const [location, setLocation] = useState(searchParams?.get("location") || "all-locations");
  const [source, setSource] = useState(searchParams?.get("source") || "all-platforms");
  const [dateRange, setDateRange] = useState(searchParams?.get("dateRange") || "any-time");
  
  // Apply filters via URL or callback
  const applyFilters = (filters: FilterState) => {
    // Build query string
    const params = new URLSearchParams();
    if (filters.searchTerm) params.set("search", filters.searchTerm);
    if (filters.location !== "all-locations") params.set("location", filters.location);
    if (filters.source !== "all-platforms") params.set("source", filters.source);
    if (filters.dateRange !== "any-time") params.set("dateRange", filters.dateRange);
    
    // Update URL to reflect filters
    router.push(`/?${params.toString()}`);
    
    // Call the callback if provided
    if (onFilterChange) {
      onFilterChange(filters);
    }
  };
  
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    applyFilters({ searchTerm, location, source, dateRange });
  };
  
  const handleReset = () => {
    setSearchTerm("");
    setLocation("all-locations");
    setSource("all-platforms");
    setDateRange("any-time");
    
    // Apply reset filters
    applyFilters({
      searchTerm: "",
      location: "all-locations",
      source: "all-platforms",
      dateRange: "any-time"
    });
  };
  
  // Update local state when URL params change, but only on initial mount or 
  // when the URL is changed from outside this component
  useEffect(() => {
    // Skip this effect on initial mount since we've already set initial state from URL params
    if (isInitialMount.current) {
      isInitialMount.current = false;
      
      // Notify parent component about initial filters on mount
      if (onFilterChange) {
        onFilterChange({
          searchTerm,
          location,
          source,
          dateRange
        });
      }
      return;
    }
    
    // Get current URL parameters
    const search = searchParams?.get("search") || "";
    const locationParam = searchParams?.get("location") || "all-locations";
    const sourceParam = searchParams?.get("source") || "all-platforms";
    const dateRangeParam = searchParams?.get("dateRange") || "any-time";
    
    // Only update state if values are different than current state
    // to prevent unnecessary re-renders and potential loops
    if (searchTerm !== search) setSearchTerm(search);
    if (location !== locationParam) setLocation(locationParam);
    if (source !== sourceParam) setSource(sourceParam);
    if (dateRange !== dateRangeParam) setDateRange(dateRangeParam);
    
  }, [searchParams, searchTerm, location, source, dateRange, onFilterChange]);
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Filter Hackathons</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="search">Search</Label>
            <Input
              id="search"
              placeholder="Search hackathons..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="location">Location</Label>
            <Select value={location} onValueChange={setLocation}>
              <SelectTrigger id="location">
                <SelectValue placeholder="Select location" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all-locations">All Locations</SelectItem>
                <SelectItem value="Mumbai">Mumbai</SelectItem>
                <SelectItem value="Delhi">Delhi</SelectItem>
                <SelectItem value="Bangalore">Bangalore</SelectItem>
                <SelectItem value="Online">Online</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="source">Platform</Label>
            <Select value={source} onValueChange={setSource}>
              <SelectTrigger id="source">
                <SelectValue placeholder="Select platform" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all-platforms">All Platforms</SelectItem>
                <SelectItem value="Unstop">Unstop</SelectItem>
                <SelectItem value="Devfolio">Devfolio</SelectItem>
                <SelectItem value="Devpost">Devpost</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="dateRange">Date Range</Label>
            <Select value={dateRange} onValueChange={setDateRange}>
              <SelectTrigger id="dateRange">
                <SelectValue placeholder="Select date range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any-time">Any Time</SelectItem>
                <SelectItem value="upcoming">Upcoming</SelectItem>
                <SelectItem value="past-events">Past Events</SelectItem>
                <SelectItem value="this-week">This Week</SelectItem>
                <SelectItem value="this-month">This Month</SelectItem>
                <SelectItem value="next-month">Next Month</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="flex flex-col gap-2 pt-2">
            <Button type="submit">Apply Filters</Button>
            <Button type="button" variant="outline" onClick={handleReset}>
              Reset Filters
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}