"use client";

import React from "react";

// Test the most basic imports first
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function TestPage() {
  return (
    <div>
      <Card>
        <h1>Test Page</h1>
        <Button>Test Button</Button>
      </Card>
    </div>
  );
}