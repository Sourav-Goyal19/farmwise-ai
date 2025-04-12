import React from "react";
import { Link } from "react-router-dom";
import { Sprout, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";

const LandingNavbar = () => {
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  return (
    <nav className="bg-white/90 backdrop-blur-sm sticky top-0 z-50 border-b border-farm-green/10">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <Sprout className="h-6 w-6 text-farm-green" />
            <span className="text-xl font-bold text-farm-green-dark">
              FarmWise
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              to="/"
              className="text-gray-700 hover:text-farm-green transition-colors"
            >
              Home
            </Link>
            <Link
              to="#features"
              className="text-gray-700 hover:text-farm-green transition-colors"
            >
              Features
            </Link>
            <Link
              to="#about"
              className="text-gray-700 hover:text-farm-green transition-colors"
            >
              About
            </Link>
            <Link
              to="#contact"
              className="text-gray-700 hover:text-farm-green transition-colors"
            >
              Contact
            </Link>
          </div>

          {/* CTA Buttons */}
          <div className="hidden md:flex items-center space-x-4">
            <Link to="/chat">
              <Button
                variant="outline"
                className="border-farm-green text-farm-green hover:bg-farm-green hover:text-white"
              >
                Chat
              </Button>
            </Link>
            <Link to="/subsidy">
              <Button className="bg-farm-green text-white hover:bg-farm-green-dark">
                Apply for Subsidy
              </Button>
            </Link>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              aria-label="Toggle menu"
            >
              {isMenuOpen ? (
                <X className="h-6 w-6 text-farm-green" />
              ) : (
                <Menu className="h-6 w-6 text-farm-green" />
              )}
            </Button>
          </div>
        </div>

        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="md:hidden pt-4 pb-6 space-y-4 animate-fade-in-up">
            <Link
              to="/"
              className="block py-2 px-4 text-gray-700 hover:bg-farm-green-light rounded-md"
              onClick={() => setIsMenuOpen(false)}
            >
              Home
            </Link>
            <Link
              to="#features"
              className="block py-2 px-4 text-gray-700 hover:bg-farm-green-light rounded-md"
              onClick={() => setIsMenuOpen(false)}
            >
              Features
            </Link>
            <Link
              to="#about"
              className="block py-2 px-4 text-gray-700 hover:bg-farm-green-light rounded-md"
              onClick={() => setIsMenuOpen(false)}
            >
              About
            </Link>
            <Link
              to="#contact"
              className="block py-2 px-4 text-gray-700 hover:bg-farm-green-light rounded-md"
              onClick={() => setIsMenuOpen(false)}
            >
              Contact
            </Link>
            <div className="pt-2 flex flex-col space-y-2">
              <Link to="/chat" onClick={() => setIsMenuOpen(false)}>
                <Button
                  variant="outline"
                  className="w-full border-farm-green text-farm-green hover:bg-farm-green hover:text-white"
                >
                  Chat
                </Button>
              </Link>
              <Link to="/subsidy" onClick={() => setIsMenuOpen(false)}>
                <Button className="w-full bg-farm-green text-white hover:bg-farm-green-dark">
                  Apply for Subsidy
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default LandingNavbar;
