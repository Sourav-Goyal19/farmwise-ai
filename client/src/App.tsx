import "./App.css";
import { AgriculturalSubsidyForm } from "./components/subsidy-form";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

function App() {
  return (
    <div className="p-12">
      <Router>
        <a href="/subsidy">Subsidy</a>
        <Routes>
          <Route path="/subsidy" element={<AgriculturalSubsidyForm />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;
