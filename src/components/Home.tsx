import React from 'react';
import { Link } from 'react-router-dom';
import { MessageSquare, Leaf, BookOpen } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-green-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-12 text-green-800">
          🌾 Welcome to AgriChat
        </h1>
        
        <div className="grid md:grid-cols-2 gap-6">
          <Link
            to="/chat"
            className="bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow"
          >
            <div className="flex items-center gap-4 mb-4">
              <MessageSquare className="w-8 h-8 text-green-600" />
              <h2 className="text-2xl font-semibold text-gray-800">Chat Assistant</h2>
            </div>
            <p className="text-gray-600">
              Get expert advice on farming, crops, and agricultural practices through our AI-powered chat assistant.
            </p>
          </Link>

          <Link
            to="/resources"
            className="bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow"
          >
            <div className="flex items-center gap-4 mb-4">
              <BookOpen className="w-8 h-8 text-green-600" />
              <h2 className="text-2xl font-semibold text-gray-800">Resources</h2>
            </div>
            <p className="text-gray-600">
              Access educational materials, guides, and documentation about sustainable farming practices.
            </p>
          </Link>
        </div>

        <div className="mt-12 bg-white p-6 rounded-lg shadow-lg">
          <div className="flex items-center gap-4 mb-4">
            <Leaf className="w-8 h-8 text-green-600" />
            <h2 className="text-2xl font-semibold text-gray-800">Latest Updates</h2>
          </div>
          <div className="space-y-4">
            <div className="border-l-4 border-green-500 pl-4">
              <h3 className="font-semibold text-gray-800">New Crop Recommendations</h3>
              <p className="text-gray-600">Updated seasonal crop recommendations now available.</p>
            </div>
            <div className="border-l-4 border-green-500 pl-4">
              <h3 className="font-semibold text-gray-800">Market Prices</h3>
              <p className="text-gray-600">Daily updates on agricultural commodity prices.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}