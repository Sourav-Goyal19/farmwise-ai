{/* Move the entire chat component here */}
import React, { useState, useCallback } from 'react';
import { Mic, Send, StopCircle, Volume2, Languages } from 'lucide-react';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { marked } from 'marked';
import sanitizeHtml from 'sanitize-html';

// Types
interface Message {
  role: 'user' | 'assistant';
  content: string;
  id: number;
}

interface Language {
  name: string;
  code: string;
}

const languages: Language[] = [
  { name: "English", code: "en" },
  { name: "Hindi", code: "hi" },
  { name: "Tamil", code: "ta" },
  { name: "Telugu", code: "te" },
  { name: "Bengali", code: "bn" },
  { name: "Marathi", code: "mr" },
  { name: "Gujarati", code: "gu" },
  { name: "Kannada", code: "kn" },
  { name: "Malayalam", code: "ml" }
];

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(import.meta.env.VITE_GOOGLE_API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" });

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState(languages[0]);
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Text-to-speech function
  const speak = useCallback((text: string, langCode: string) => {
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langCode;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find(v => 
      v.lang.startsWith(langCode) && 
      (v.name.includes("Google") || v.name.includes("Male") || v.name.includes("Indian"))
    ) || voices.find(v => v.lang.startsWith(langCode)) || voices[0];

    if (voice) {
      utterance.voice = voice;
    }

    window.speechSynthesis.speak(utterance);
  }, []);

  // Stop speech function
  const stopSpeech = useCallback(() => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, []);

  // Parse Markdown and sanitize HTML
  const renderMessageContent = (content: string) => {
    const markdown = marked(content);
    const sanitized = sanitizeHtml(markdown, {
      allowedTags: ['p', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br'],
      allowedAttributes: {},
    });
    return { __html: sanitized };
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      id: messages.length,
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const prompt = `You are an agricultural expert specializing in crops, farming challenges, government schemes for farmers, and current market prices for crops. Provide detailed and helpful information to assist farmers. Assist them and talk like a human, with proper punctuation and expression. Format your response using Markdown for clarity, with proper headings, bullet points, and numbered lists where appropriate.

User question: ${inputMessage}`;

      const result = await model.generateContent(prompt);
      const response = await result.response;
      const text = response.text();

      const assistantMessage: Message = {
        role: 'assistant',
        content: text,
        id: messages.length + 1,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error generating response:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'I apologize, but I encountered an error while processing your request. Please try again.',
        id: messages.length + 1,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-green-100">
      {/* Rest of your component JSX */}
      {/* Sidebar */}
      <div className="fixed left-0 top-0 h-full w-64 bg-white shadow-lg p-4">
        <div className="flex items-center gap-2 mb-6">
          <Languages className="w-6 h-6 text-green-600" />
          <h2 className="text-lg font-semibold">Language</h2>
        </div>
        <div className="space-y-2">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => setSelectedLanguage(lang)}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                selectedLanguage.code === lang.code
                  ? "bg-green-100 text-green-700"
                  : "hover:bg-gray-100"
              }`}
            >
              {lang.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="ml-64 h-screen flex flex-col">
        {/* Header */}
        <header className="bg-white shadow-sm p-4 flex items-center gap-3">
          <img
            src="https://images.unsplash.com/photo-1495107334309-fcf20504a5ab?auto=format&fit=crop&q=80&w=32&h=32"
            alt="AgriChat"
            className="w-8 h-8 rounded-full"
          />
          <h1 className="text-xl font-bold text-gray-800">
            🌾 AgriChat: Your Agricultural Assistant
          </h1>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-4 ${
                  message.role === "user"
                    ? "bg-green-600 text-white"
                    : "bg-white text-gray-800"
                } shadow-sm`}
              >
                {message.role === "assistant" ? (
                  <div
                    className="prose prose-sm max-w-none"
                    dangerouslySetInnerHTML={renderMessageContent(
                      message.content
                    )}
                  />
                ) : (
                  <p>{message.content}</p>
                )}
                {message.role === "assistant" && (
                  <div className="mt-2 flex items-center gap-2">
                    <button
                      className={`text-green-600 hover:text-green-700 flex items-center gap-1 text-sm ${
                        isSpeaking ? "text-red-600 hover:text-red-700" : ""
                      }`}
                      onClick={() => {
                        if (isSpeaking) {
                          stopSpeech();
                        } else {
                          const plainText = message.content.replace(
                            /[*_#]+/g,
                            ""
                          );
                          speak(plainText, selectedLanguage.code);
                        }
                      }}
                    >
                      <Volume2 className="w-4 h-4" />
                      {isSpeaking ? "Stop Reading" : "Read Aloud"}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white text-gray-800 rounded-lg p-4 shadow-sm max-w-[80%]">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2 h-2 bg-green-600 rounded-full animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  />
                  <div
                    className="w-2 h-2 bg-green-600 rounded-full animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <div
                    className="w-2 h-2 bg-green-600 rounded-full animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="bg-white border-t p-4">
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <button
              type="button"
              onClick={() => setIsRecording(!isRecording)}
              className={`p-2 rounded-full ${
                isRecording
                  ? "bg-red-100 text-red-600"
                  : "bg-gray-100 text-gray-600"
              } hover:bg-opacity-80 transition-colors`}
            >
              {isRecording ? (
                <StopCircle className="w-6 h-6" />
              ) : (
                <Mic className="w-6 h-6" />
              )}
            </button>
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your question here..."
              className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isLoading}
              className="bg-green-600 text-white p-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-6 h-6" />
            </button>
          </form>
        </div>
      </div>

      {/* Inline CSS for Prose */}
      <style>{`
        .prose {
          color: inherit;
          line-height: 1.75;
        }
        .prose h1, .prose h2, .prose h3, .prose h4, .prose h5, .prose h6 {
          margin-top: 1.25em;
          margin-bottom: 0.75em;
          font-weight: 600;
          color: #1a202c;
        }
        .prose ul, .prose ol {
          margin-top: 1em;
          margin-bottom: 1em;
          padding-left: 1.5em;
        }
        .prose li {
          margin-top: 0.5em;
          margin-bottom: 0.5em;
        }
        .prose p {
          margin-top: 1em;
          margin-bottom: 1em;
        }
        .prose strong {
          font-weight: 600;
        }
        .prose em {
          font-style: italic;
        }
      `}</style>
    </div>
  );
}