import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import Dashboard from './pages/Dashboard';
import NewEvaluation from './pages/NewEvaluation';
import EvaluationResults from './pages/EvaluationResults';
import History from './pages/History';
import Comparison from './pages/Comparison';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import AutomatedEvaluation from './pages/AutomatedEvaluation';
import EvaluationRuns from './pages/EvaluationRuns';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="evaluate" element={<NewEvaluation />} />
          <Route path="evaluate/:id" element={<NewEvaluation />} />
          <Route path="automated-evaluation" element={<AutomatedEvaluation />} />
          <Route path="evaluation-runs" element={<EvaluationRuns />} />
          <Route path="results/:id" element={<EvaluationResults />} />
          <Route path="history" element={<History />} />
          <Route path="comparison" element={<Comparison />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
