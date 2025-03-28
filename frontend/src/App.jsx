import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import AuthCallback from "@/components/AuthCallback";
function App() {
  return (
    <>
      <div className="min-h-screen bg-gray-100 p-4">
        <Dashboard />
      </div>

      <Router>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
        </Routes>
      </Router>
    </>
  );
}

export default App;
