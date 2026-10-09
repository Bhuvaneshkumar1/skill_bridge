import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import OnboardingModal from './components/OnboardingModal';
import AgentChatDrawer from './components/AgentChatDrawer';
import ErrorBoundary from './components/ErrorBoundary';

import Dashboard from './pages/Dashboard';
import LearningSession from './pages/LearningSession';
import SkillAnalyzer from './pages/SkillAnalyzer';
import ResourceFinder from './pages/ResourceFinder';
import CodeSandbox from './pages/CodeSandbox';
import QuizPage from './pages/QuizPage';
import { api } from './api/client';

export default function App() {
  const [currentProfile, setCurrentProfile] = useState(null);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(true);

  useEffect(() => {
    const savedId = localStorage.getItem('skillbridge_student_id');
    if (!savedId) {
      // FORCE ONBOARDING IF USER HAS NOT SET NAME AND CAREER GOAL YET!
      setCurrentProfile(null);
      setIsOnboardingOpen(true);
      setLoadingProfile(false);
      return;
    }

    api.getProfile(parseInt(savedId, 10))
      .then((profile) => {
        setCurrentProfile(profile);
      })
      .catch(() => {
        setIsOnboardingOpen(true);
      })
      .finally(() => {
        setLoadingProfile(false);
      });
  }, []);

  const handleProfileCreated = (profile) => {
    setCurrentProfile(profile);
    if (profile?.id) {
      localStorage.setItem('skillbridge_student_id', profile.id.toString());
    }
  };

  return (
    <Router>
      <div className="min-h-screen bg-[#0B0F17] text-gray-100 flex flex-col font-sans">
        
        {/* Navigation Bar */}
        <Navbar
          currentProfile={currentProfile}
          onOpenOnboarding={() => setIsOnboardingOpen(true)}
        />

        {/* Main Content View Router */}
        <main className="flex-1 pb-16">
          <ErrorBoundary>
            <Routes>
              <Route
                path="/"
                element={
                  <Dashboard
                    currentStudentId={currentProfile?.id}
                    onOpenOnboarding={() => setIsOnboardingOpen(true)}
                  />
                }
              />
              <Route
                path="/session"
                element={<LearningSession currentStudentId={currentProfile?.id} />}
              />
              <Route
                path="/quiz"
                element={<QuizPage currentStudentId={currentProfile?.id} />}
              />
              <Route
                path="/sandbox"
                element={<CodeSandbox />}
              />
              <Route
                path="/analyzer"
                element={<SkillAnalyzer currentStudentId={currentProfile?.id} />}
              />
              <Route
                path="/resources"
                element={<ResourceFinder />}
              />
            </Routes>
          </ErrorBoundary>
        </main>

        {/* Onboarding Diagnostic Modal */}
        <OnboardingModal
          isOpen={isOnboardingOpen}
          onClose={() => setIsOnboardingOpen(false)}
          onProfileCreated={handleProfileCreated}
        />

        {/* Floating AI Agent Chat Drawer */}
        <AgentChatDrawer currentStudentId={currentProfile?.id} />

      </div>
    </Router>
  );
}
