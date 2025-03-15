"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function HackathonFilters() {
  const [searchTerm, setSearchTerm] = useState("");
  const [location, setLocation] = useState("all-locations");
  const [source, setSource] = useState("all-platforms");
  const [dateRange, setDateRange] = useState("any-time");
  
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    
    // In a real app, this would update a global state or URL parameters
    // to filter the hackathons list
    console.log("Filtering with:", { searchTerm, location, source, dateRange });
  };
  
  const handleReset = () => {
    setSearchTerm("");
    setLocation("all-locations");
    setSource("all-platforms");
    setDateRange("any-time");
  };
  
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
            <Label htmlFor="date-range">Date Range</Label>
            <Select value={dateRange} onValueChange={setDateRange}>
              <SelectTrigger id="date-range">
                <SelectValue placeholder="Select date range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any-time">Any Time</SelectItem>
                <SelectItem value="upcoming">Upcoming</SelectItem>
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