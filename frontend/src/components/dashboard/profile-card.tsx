"use client";

import React from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Upload, Sparkles, Heart, Star } from "lucide-react";

export default function ProfileCard() {
  const [isDragOver, setIsDragOver] = React.useState(false);
  const [uploadState, setUploadState] = React.useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [showSuccess, setShowSuccess] = React.useState(false);
  const [formData, setFormData] = React.useState({
    name: 'John Doe',
    username: 'johndoe',
    role: 'admin',
    department: 'engineering'
  });
  
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };
  
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };
  
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    setUploadState('uploading');
    
    // Simulate upload
    await new Promise(resolve => setTimeout(resolve, 2000));
    setUploadState('success');
    
    setTimeout(() => setUploadState('idle'), 3000);
  };
  
  const handleSave = () => {
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 2000);
  };

  return (
    <Card className="card-hover shadow-soft">
      <CardHeader className="bg-gradient-to-r from-orange-50 to-pink-50 border-b">
        <CardTitle className="gradient-text text-xl">Public Profile</CardTitle>
        <CardDescription className="text-muted-foreground/80">
          Customize your public profile information and preferences.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form className="grid gap-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input 
                id="name" 
                placeholder="Enter your name" 
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="transition-all duration-200 focus:scale-[1.02] hover:shadow-sm"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input 
                id="username" 
                placeholder="Enter your username"
                value={formData.username}
                onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                className="transition-all duration-200 focus:scale-[1.02] hover:shadow-sm"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Role</Label>
            <Select value={formData.role} onValueChange={(value) => setFormData(prev => ({ ...prev, role: value }))}>
              <SelectTrigger className="transition-all duration-200 hover:shadow-sm focus:scale-[1.02]">
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="admin">🔑 Admin</SelectItem>
                <SelectItem value="editor">✏️ Editor</SelectItem>
                <SelectItem value="viewer">👁️ Viewer</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Department</Label>
            <Select value={formData.department} onValueChange={(value) => setFormData(prev => ({ ...prev, department: value }))}>
              <SelectTrigger className="transition-all duration-200 hover:shadow-sm focus:scale-[1.02]">
                <SelectValue placeholder="Select a department" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="engineering">⚙️ Engineering</SelectItem>
                <SelectItem value="design">🎨 Design</SelectItem>
                <SelectItem value="marketing">📈 Marketing</SelectItem>
                <SelectItem value="sales">💼 Sales</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Profile Picture</Label>
            <div className="flex items-center gap-4">
              <Avatar className={`h-16 w-16 transition-all duration-300 ${
                uploadState === 'success' ? 'animate-bounce-gentle ring-4 ring-green-200' : ''
              } ${
                uploadState === 'uploading' ? 'animate-pulse' : ''
              }`}>
                <AvatarImage src="https://picsum.photos/id/1005/100/100" data-ai-hint="woman face" />
                <AvatarFallback>AV</AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div 
                  className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer group transition-all duration-300 ${
                    isDragOver 
                      ? 'border-green-400 bg-green-50 scale-105 shadow-lg' 
                      : uploadState === 'uploading'
                      ? 'border-orange-300 bg-orange-50 animate-pulse'
                      : uploadState === 'success'
                      ? 'border-green-300 bg-green-50 animate-bounce-gentle'
                      : uploadState === 'error'
                      ? 'border-red-300 bg-red-50'
                      : 'border-orange-200 bg-orange-50/50 hover:border-orange-300 hover:bg-orange-50 hover:scale-[1.02]'
                  }`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  {uploadState === 'uploading' ? (
                    <div className="space-y-2">
                      <div className="flex justify-center space-x-1">
                        <div className="w-2 h-2 bg-orange-500 rounded-full animate-loading-dots" />
                        <div className="w-2 h-2 bg-pink-500 rounded-full animate-loading-dots" style={{ animationDelay: '0.2s' }} />
                        <div className="w-2 h-2 bg-purple-500 rounded-full animate-loading-dots" style={{ animationDelay: '0.4s' }} />
                      </div>
                      <p className="text-sm text-orange-600 font-medium">Uploading your awesome photo...</p>
                    </div>
                  ) : uploadState === 'success' ? (
                    <div className="space-y-2">
                      <Sparkles className="mx-auto h-8 w-8 text-green-500 animate-sparkle" />
                      <p className="text-sm text-green-600 font-medium">Perfect! Looking great! ✨</p>
                    </div>
                  ) : (
                    <>
                      <Upload className={`mx-auto h-8 w-8 transition-all duration-300 ${
                        isDragOver 
                          ? 'text-green-500 animate-bounce' 
                          : 'text-orange-500 group-hover:text-orange-600 group-hover:animate-wiggle'
                      }`} />
                      <p className="mt-2 text-sm text-foreground">
                        <span className="font-semibold text-orange-600">
                          {isDragOver ? 'Drop it like it\'s hot! 🔥' : 'Click to upload'}
                        </span>{" "}
                        {!isDragOver && 'or drag and drop'}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        PNG, JPG, GIF up to 10MB
                      </p>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </form>
      </CardContent>
      <CardFooter className="border-t bg-muted/20 px-6 py-4">
        <div className="flex gap-3">
          <Button 
            variant={showSuccess ? 'success' : 'celebration'}
            className={`transition-all duration-300 ${showSuccess ? 'animate-heartbeat' : ''}`}
            onClick={handleSave}
          >
            {showSuccess ? (
              <>
                <Heart className="h-4 w-4 mr-2" />
                Saved! ✨
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
          <Button variant="outline" className="hover:animate-wiggle">Reset</Button>
        </div>
      </CardFooter>
    </Card>
  );
}