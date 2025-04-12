import "./App.css";
import Chat from "./components/chat";
import LandingPage from "./components/home";
import { AgriculturalSubsidyForm } from "./components/subsidy-form";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

function App() {
  return (
    <div className="p-">
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/subsidy" element={<AgriculturalSubsidyForm />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;
