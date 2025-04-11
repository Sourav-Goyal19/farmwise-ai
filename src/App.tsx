import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Home as HomeIcon, MessageSquare, BookOpen } from 'lucide-react';
import Home from './components/Home';
import Chat from './components/Chat';
import Resources from './components/Resources';

function App() {
  return (
    <Router>
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 bg-white shadow-md z-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2 text-green-600 font-bold text-xl">
              🌾 AgriChat
            </Link>
            <div className="flex gap-4">
              <Link
                to="/"
                className="flex items-center gap-2 px-3 py-2 rounded-md text-gray-600 hover:text-green-600 hover:bg-green-50"
              >
                <HomeIcon className="w-5 h-5" />
                <span>Home</span>
              </Link>
              <Link
                to="/chat"
                className="flex items-center gap-2 px-3 py-2 rounded-md text-gray-600 hover:text-green-600 hover:bg-green-50"
              >
                <MessageSquare className="w-5 h-5" />
                <span>Chat</span>
              </Link>
              <Link
                to="/resources"
                className="flex items-center gap-2 px-3 py-2 rounded-md text-gray-600 hover:text-green-600 hover:bg-green-50"
              >
                <BookOpen className="w-5 h-5" />
                <span>Resources</span>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-16">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/resources" element={<Resources />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;