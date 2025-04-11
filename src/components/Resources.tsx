import React from 'react';
import { Book, Download, ExternalLink } from 'lucide-react';

export default function Resources() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-green-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-12 text-green-800">
          Agricultural Resources
        </h1>

        <div className="grid gap-8">
          <section className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-4 mb-6">
              <Book className="w-8 h-8 text-green-600" />
              <h2 className="text-2xl font-semibold text-gray-800">Farming Guides</h2>
            </div>
            <div className="space-y-4">
              {[
                {
                  title: "Sustainable Farming Practices",
                  description: "Learn about eco-friendly farming methods and techniques.",
                },
                {
                  title: "Crop Disease Management",
                  description: "Comprehensive guide on identifying and treating common crop diseases.",
                },
                {
                  title: "Water Conservation in Agriculture",
                  description: "Best practices for efficient water usage in farming.",
                },
              ].map((guide, index) => (
                <div key={index} className="border-l-4 border-green-500 pl-4">
                  <h3 className="font-semibold text-gray-800">{guide.title}</h3>
                  <p className="text-gray-600 mb-2">{guide.description}</p>
                  <button className="text-green-600 hover:text-green-700 flex items-center gap-2">
                    <Download className="w-4 h-4" />
                    Download PDF
                  </button>
                </div>
              ))}
            </div>
          </section>

          <section className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-4 mb-6">
              <ExternalLink className="w-8 h-8 text-green-600" />
              <h2 className="text-2xl font-semibold text-gray-800">External Resources</h2>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              {[
                {
                  title: "Government Agricultural Portal",
                  description: "Official government resources and schemes for farmers.",
                  link: "#",
                },
                {
                  title: "Weather Services",
                  description: "Agricultural weather forecasting and alerts.",
                  link: "#",
                },
                {
                  title: "Market Prices Database",
                  description: "Real-time agricultural commodity prices.",
                  link: "#",
                },
                {
                  title: "Farmer Community Forum",
                  description: "Connect with other farmers and share experiences.",
                  link: "#",
                },
              ].map((resource, index) => (
                <a
                  key={index}
                  href={resource.link}
                  className="block p-4 border border-gray-200 rounded-lg hover:border-green-500 transition-colors"
                >
                  <h3 className="font-semibold text-gray-800">{resource.title}</h3>
                  <p className="text-gray-600">{resource.description}</p>
                </a>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}